"""Shared recurrent PPO with isolated per-hero state and short on-policy rollouts.

The GRU sees connectome motor features, not a bypass around the fly graph.
This is an engineered recurrent learner, not whole-brain biological plasticity.
"""
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical

torch.set_num_threads(2)

class RecurrentPolicy(nn.Module):
    def __init__(self,features,actions,hidden=64):
        super().__init__();self.hidden=hidden;self.actions=actions
        self.register_buffer("feature_mean",torch.zeros(features))
        self.register_buffer("feature_scale",torch.ones(features))
        self.cell=nn.GRUCell(features,hidden)
        self.actor=nn.Linear(hidden,actions);self.critic=nn.Linear(hidden,1)
    def forward(self,x,h,legal):
        x=((x-self.feature_mean)/self.feature_scale).clamp(-10,10)
        x=x/x.norm(dim=-1,keepdim=True).clamp_min(1e-8)
        h=self.cell(x,h)
        logits=self.actor(h).masked_fill(~legal,-1e9)
        return Categorical(logits=logits),self.critic(h).squeeze(-1),h

class SharedPPO:
    def __init__(self,features,actions,hidden=64,rollout=256,seed=0,learning=True):
        torch.manual_seed(seed)
        self.policy=RecurrentPolicy(features,actions,hidden)
        self.optimizer=torch.optim.Adam(self.policy.parameters(),lr=3e-4)
        self.rollout=rollout;self.learning=learning;self.version=0;self.samples=0
        self.buffers=defaultdict(list);self.states={};self.pending={}
        self.total_reward=0.;self.stats={};self.dropped_stale=0
    def reset(self,key):
        self.states.pop(key,None);self.pending.pop(key,None)
        self.buffers.pop(key,None)
    def act(self,key,features,legal,reward=0.,done=False,elapsed=1.):
        x=torch.as_tensor(np.asarray(features),dtype=torch.float32).reshape(1,-1)
        mask=torch.as_tensor(legal,dtype=torch.bool).reshape(1,-1)
        h=self.states.get(key,torch.zeros(1,self.policy.hidden))
        with torch.no_grad():dist,value,hn=self.policy(x,h,mask)
        previous=self.pending.pop(key,None)
        self.total_reward+=reward
        if previous is not None and self.learning:
            if previous['version']==self.version:
                previous.update(reward=float(reward)*.1,done=done,elapsed=elapsed,next_value=0. if done else value.item())
                self.buffers[key].append(previous);self.samples+=1
            else:self.dropped_stale+=1
        if sum(map(len,self.buffers.values()))>=self.rollout:
            self.update()
            with torch.no_grad():dist,value,hn=self.policy(x,h,mask)
        if done:
            self.states.pop(key,None)
            return 0,dict(memory_norm=0.,probabilities=mask[0].float().tolist())
        action=dist.sample() if self.learning else dist.probs.argmax(-1)
        self.states[key]=hn.detach()
        self.pending[key]=dict(x=x[0].clone(),h=h[0].clone(),mask=mask[0].clone(),action=action.item(),
            logp=dist.log_prob(action).item(),value=value.item(),version=self.version)
        return action.item(),dict(memory_norm=hn.norm().item(),probabilities=dist.probs[0].tolist())
    def update(self):
        sequences=[];advantages=[]
        for rows in self.buffers.values():
            gae=0.
            for row in reversed(rows):
                discount=.99**row['elapsed'];trace=.95**row['elapsed'];alive=not row['done']
                delta=row['reward']+discount*row['next_value']-row['value']
                gae=delta+discount*trace*alive*gae
                row['adv']=gae;row['return']=gae+row['value'];advantages.append(gae)
            for start in range(0,len(rows),32):sequences.append(rows[start:start+32])
        if not advantages:return
        mean=float(np.mean(advantages));std=max(float(np.std(advantages)),1e-6)
        losses=[];before=torch.cat([p.detach().flatten() for p in self.policy.parameters()]).clone()
        for _ in range(3):
            self.optimizer.zero_grad();loss=0.;count=0
            for rows in sequences:
                h=rows[0]['h'].reshape(1,-1).detach()
                for row in rows:
                    dist,value,h=self.policy(row['x'][None],h,row['mask'][None])
                    logp=dist.log_prob(torch.tensor([row['action']]))
                    ratio=(logp-row['logp']).exp();adv=(row['adv']-mean)/std
                    actor=-torch.minimum(ratio*adv,ratio.clamp(.8,1.2)*adv)
                    loss=loss+actor.mean()+.5*(value-row['return']).square().mean()-.01*dist.entropy().mean()
                    count+=1
                    if row['done']:h=torch.zeros_like(h)
            loss=loss/count
            if not torch.isfinite(loss):raise ValueError('Nonfinite PPO loss')
            loss.backward();nn.utils.clip_grad_norm_(self.policy.parameters(),.5);self.optimizer.step();losses.append(loss.item())
        after=torch.cat([p.detach().flatten() for p in self.policy.parameters()])
        self.version+=1;self.stats=dict(loss=float(np.mean(losses)),parameter_change=float((after-before).norm()),samples=count,streams=len(self.buffers))
        self.buffers.clear()
    def save(self,path,schema):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp')
        torch.save(dict(schema=schema,policy=self.policy.state_dict(),optimizer=self.optimizer.state_dict(),
            version=self.version,samples=self.samples,total_reward=self.total_reward,rng=torch.get_rng_state()),temp)
        temp.replace(path)
    def load(self,path,schema):
        data=torch.load(path,map_location='cpu',weights_only=True)
        if data['schema']!=schema:raise ValueError('Recurrent checkpoint schema mismatch')
        data['policy'].setdefault('feature_mean',torch.zeros_like(self.policy.feature_mean))
        data['policy'].setdefault('feature_scale',torch.ones_like(self.policy.feature_scale))
        self.policy.load_state_dict(data['policy']);self.optimizer.load_state_dict(data['optimizer'])
        self.version=data['version'];self.samples=data['samples'];self.total_reward=data['total_reward']
        torch.set_rng_state(data['rng'])
