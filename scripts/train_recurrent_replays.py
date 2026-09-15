"""Bounded pro replay warm-start. Labels are activity proxies, not complete expert actions."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from fruit_fly_dota.schema import OBS_SIZE,ACTION_COUNT,SCHEMA
from fruit_fly_dota.recurrent import SharedPPO
from fruit_fly_dota.full_neural import FullReservoir
from fruit_fly_dota.malecns import load_full
from fruit_fly_dota.train_sf import examples

def main():
    p=argparse.ArgumentParser();p.add_argument('--from-cache',action='store_true');p.add_argument('--per-match',type=int,default=600);p.add_argument('--epochs',type=int,default=15);p.add_argument('--output',default='work/shared-v6.pt');a=p.parse_args()
    out=Path(a.output)
    if out.exists():raise ValueError('Refusing to overwrite an existing recurrent policy')
    cache=Path('work/recurrent-pro-features.npz');manifest=json.loads(Path('data/replays/sf_manifest.json').read_text());data=[];provenance=[]
    if a.from_cache:
        with np.load(cache,allow_pickle=False) as saved:
            i=0
            while f'{i}_x' in saved:
                data.append((str(saved[f'{i}_split']),saved[f'{i}_x'],saved[f'{i}_y'],saved[f'{i}_reset'].tolist()));i+=1
        provenance=json.loads(Path('results/recurrent/imitation.json').read_text())['provenance']
    else:
        w,s,m,g=load_full();brain=FullReservoir(w,s,m,input_size=OBS_SIZE,legacy_input_size=33)
        for match in manifest['matches']:
            if not match.get('player'):continue
            path=Path('data/replays/parsed')/(str(match['match_id'])+'.jsonl')
            rows=[json.loads(l) for l in path.read_text().splitlines()]
            samples=examples(rows,limit=1000000)[:a.per_match]
            if len(samples)<100:continue
            features=[];resets=[];previous=None;brain.reset()
            print('Encoding',match['player'],len(samples),match['split'],flush=True)
            for i,(tick,x,y,source) in enumerate(samples):
                reset=previous is None or tick-previous!=30
                if reset:brain.reset()
                obs=np.zeros(OBS_SIZE,dtype=np.float32);obs[:5]=x[:5]
                features.append(brain.features(obs)[:-1]);resets.append(reset);previous=tick
                if i%200==199:print('encoded',i+1,flush=True)
            data.append((match['split'],np.array(features,dtype=np.float32),np.array([s[2] for s in samples]),resets))
            provenance.append(dict(match=match['match_id'],player=match['player'],split=match['split'],samples=len(samples),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        np.savez_compressed(cache,**{f'{i}_{kind}':value for i,(split,x,y,r) in enumerate(data) for kind,value in [('x',x),('y',y),('reset',np.array(r)),('split',np.array(split))]})
    learner=SharedPPO(64,ACTION_COUNT);policy=learner.policy
    training_features=np.concatenate([x for split,x,y,r in data if split=='train'])
    policy.feature_mean.copy_(torch.tensor(training_features.mean(axis=0)))
    policy.feature_scale.copy_(torch.tensor(training_features.std(axis=0).clip(1e-5)))
    counts=np.bincount(np.concatenate([y for split,x,y,r in data if split=='train']),minlength=14)
    weights=torch.tensor(1/np.sqrt(np.maximum(1,counts)),dtype=torch.float32)
    history=[]
    for epoch in range(a.epochs):
        losses=[]
        for split,x,y,resets in data:
            if split!='train':continue
            h=torch.zeros(1,policy.hidden)
            for start in range(0,len(y),32):
                learner.optimizer.zero_grad();loss=0.;n=0;h=h.detach()
                for i in range(start,min(start+32,len(y))):
                    if resets[i]:h=torch.zeros_like(h)
                    dist,v,h=policy(torch.tensor(x[i:i+1]),h,torch.ones(1,ACTION_COUNT,dtype=torch.bool))
                    # Unknown new actions receive no negative supervision.
                    loss=loss+F.cross_entropy(dist.logits[:,:14],torch.tensor([int(y[i])]),weight=weights);n+=1
                loss=loss/n;loss.backward();torch.nn.utils.clip_grad_norm_(policy.parameters(),.5);learner.optimizer.step();losses.append(loss.item())
        history.append(float(np.mean(losses)));print('BC epoch',epoch+1,'loss',history[-1],flush=True)
    metrics={};majority=int(counts.argmax())
    for split in ('train','validation','test'):
        labels=[];predictions={k:[] for k in ('normal','no_memory','zero_graph')}
        for s,x,y,resets in data:
            if s!=split:continue
            labels.extend(y.tolist())
            for mode in predictions:
                h=torch.zeros(1,policy.hidden)
                with torch.no_grad():
                    for i in range(len(y)):
                        if resets[i] or mode=='no_memory':h=torch.zeros_like(h)
                        features=np.zeros_like(x[i:i+1]) if mode=='zero_graph' else x[i:i+1]
                        dist,v,h=policy(torch.tensor(features),h,torch.ones(1,ACTION_COUNT,dtype=torch.bool))
                        predictions[mode].append(int(dist.logits[:,:14].argmax()))
        labels=np.array(labels);metrics[split]={'samples':len(labels),'majority_accuracy':float(np.mean(labels==majority))}
        for mode,pred in predictions.items():
            pred=np.array(pred);metrics[split][mode]=dict(accuracy=float(np.mean(pred==labels)),balanced_accuracy=float(np.mean([np.mean(pred[labels==c]==c) for c in np.unique(labels)])))
    learner.save(out,SCHEMA)
    report=dict(schema=SCHEMA,provenance=provenance,loss=history,metrics=metrics,limitations=['Own position, HP, mana and level only; other observations are missing and zero-filled','Movement inferred from displacement; attacks inferred from damage; spells from actual events','First contiguous-time 600 eligible samples per match; gaps reset recurrent states','No claim of learned rune, item, fog or full-game strategy','Evaluation masks to the 14 supported activity labels; not full action-space gameplay accuracy'])
    Path('results/recurrent').mkdir(parents=True,exist_ok=True);Path('results/recurrent/imitation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(metrics,indent=2),flush=True)
if __name__=='__main__':main()
