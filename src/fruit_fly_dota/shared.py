"""Local shared policy service. Each environment/hero owns independent neural and GRU state."""
import argparse,copy,json,time,hashlib
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import numpy as np
from .schema import OBS_SIZE,ACTION_COUNT,FEATURE_SIZE,SCHEMA
from .full_neural import FullReservoir
from .malecns import load_full
from .recurrent import SharedPPO

class SharedController:
    def __init__(self,brain,learner):
        self.prototype=brain;self.learner=learner;self.streams={};self.latest={};self.decisions=0
    def step(self,p):
        if not isinstance(p,dict):raise ValueError('Expected object')
        env=p.get('env','local');agent=p.get('agent','0');session=p.get('session','default');seq=p.get('seq')
        if any(not isinstance(v,str) or not 1<=len(v)<=64 or not all(c.isalnum() or c in '-_.' for c in v) for v in (env,agent,session)):raise ValueError('Invalid stream identifiers')
        if type(seq) is not int or not 0<=seq<2**31:raise ValueError('Invalid sequence')
        obs=np.asarray(p.get('obs'),dtype=np.float32);legal=p.get('legal')
        if obs.shape!=(OBS_SIZE,) or not np.isfinite(obs).all() or np.max(abs(obs))>10:raise ValueError('Invalid observation')
        if not isinstance(legal,list) or len(legal)!=ACTION_COUNT or legal[0]!=1 or any(type(v) is not int or v not in (0,1) for v in legal):raise ValueError('Invalid legal mask')
        reward=p.get('reward',0);dt=p.get('dt',1);done=p.get('terminal',False);boundary=p.get('round_end',False)
        if type(reward) not in (int,float) or not np.isfinite(reward) or abs(reward)>200:raise ValueError('Invalid reward')
        if type(dt) not in (int,float) or not np.isfinite(dt) or not 0<dt<=60:raise ValueError('Invalid duration')
        if type(done) is not bool or type(boundary) is not bool:raise ValueError('Invalid terminal')
        applied=p.get('previous_applied',True)
        if type(applied) is not bool:raise ValueError('Invalid action acknowledgement')
        if p.get('assisted',False) is not False:raise ValueError('Tactical assistance disabled')
        key=env+'/'+agent
        if key not in self.streams:
            if len(self.streams)>=256:raise ValueError('Stream capacity reached')
            brain=copy.copy(self.prototype);brain.reset()
            self.streams[key]=dict(brain=brain,session=session,seq=-1,reward=0.,rounds=0)
        state=self.streams[key]
        if state['session']!=session:
            state.update(session=session,seq=-1,reward=0.,rounds=0);state['brain'].reset();self.learner.reset(key)
        fingerprint=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
        if seq==state['seq'] and state.get('fingerprint')==fingerprint:return state['result']
        if seq<=state['seq']:raise ValueError('Stale sequence')
        if not applied:
            # A timed-out or rejected order is not an executed policy action.
            # Discard this stream's short rollout so returns cannot cross the gap.
            self.learner.pending.pop(key,None);self.learner.buffers.pop(key,None)
        started=time.perf_counter();brain=state['brain']
        features=brain.features(obs)[:-1]
        if boundary:
            self.learner.act(key,features,legal,reward,done=True,elapsed=dt)
            brain.reset();features=brain.features(obs)[:-1];state['rounds']+=1
            action,info=self.learner.act(key,features,legal,0.,done=done,elapsed=dt)
        else:action,info=self.learner.act(key,features,legal,reward,done=done,elapsed=dt)
        state.update(seq=seq,reward=state['reward']+reward,last_seen=time.time());self.decisions+=1
        sample=np.linspace(0,brain.n-1,min(240,brain.n),dtype=int)
        result=dict(seq=seq,action=action,env=env,agent=agent,session=session,obs=obs.tolist(),legal=legal,
            reward=reward,previous_applied=applied,reward_components=p.get('reward_components',{}),reward_version=p.get('reward_version','shared-v5'),
            total_reward=self.learner.total_reward,learning_updates=self.learner.version,rounds=state['rounds'],
            policy='shared connectome + GRU / recurrent PPO',control_mode='neural choices; structured observations and legal masks',
            learning='GRU actor-critic and readout learn; fly connectivity fixed',wall_time=time.time(),
            decision_ms=(time.perf_counter()-started)*1000,neurons=brain.n,motor_pools=features.tolist(),activity=brain.state[sample].tolist(),
            sampled_indices=sample.tolist(),terminal=done,dt=dt,policy_version=self.learner.version,ppo=self.learner.stats,
            active_agents=sum(time.time()-v.get('last_seen',0)<10 for v in self.streams.values()),**info)
        state.update(fingerprint=fingerprint,result=result)
        self.latest=result
        return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8765);p.add_argument('--checkpoint',default='work/shared-v6.pt');p.add_argument('--log',default='work/shared-v6.jsonl');p.add_argument('--evaluate',action='store_true');a=p.parse_args()
    w,s,m,manifest=load_full();brain=FullReservoir(w,s,m,input_size=OBS_SIZE,legacy_input_size=33)
    learner=SharedPPO(FEATURE_SIZE,ACTION_COUNT,learning=not a.evaluate)
    if Path(a.checkpoint).exists():learner.load(a.checkpoint,SCHEMA)
    controller=SharedController(brain,learner);log=Path(a.log);log.parent.mkdir(parents=True,exist_ok=True)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/':body=Path(__file__).with_name('dashboard.html').read_bytes();mime='text/html; charset=utf-8'
            elif urlsplit(self.path).path=='/state':
                selected=parse_qs(urlsplit(self.path).query).get('agent',['0'])[0]
                current=controller.streams.get('local/'+selected,{}).get('result',controller.latest)
                body=json.dumps(current or {'status':'Waiting for Dota','policy_version':learner.version}).encode();mime='application/json'
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def do_POST(self):
            if self.path!='/step':self.send_error(404);return
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=32768:raise ValueError('Invalid length')
                payload=json.loads(self.rfile.read(n));result=controller.step(payload)
            except (ValueError,TypeError,OverflowError):self.send_error(400);return
            record={k:v for k,v in result.items() if k not in ('activity','sampled_indices','probabilities')}
            with log.open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
            if controller.decisions%100==0 or result['terminal']:learner.save(a.checkpoint,SCHEMA)
            body=f"{result['seq']}|{result['action']}".encode()
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    HTTPServer.request_queue_size=128
    server=HTTPServer(('127.0.0.1',a.port),Handler)
    print(f'Ready: {brain.n} neurons; shared GRU PPO; policy version {learner.version}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();learner.save(a.checkpoint,SCHEMA)
if __name__=='__main__':main()
