"""Initial pro-replay imitation: own-state only, mixed-confidence activity labels."""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from .malecns import load_full
from .full_neural import FullReservoir
from .live import OBS_SIZE, ACTION_COUNT

SELF_FIELDS=[0,1,2,3,4]
CASTS={'nevermore_shadowraze1':10,'nevermore_shadowraze2':11,'nevermore_shadowraze3':12,'nevermore_requiem':13}

def examples(rows,limit=600):
    states=sorted([r for r in rows if 'event' not in r],key=lambda r:r['tick'])
    events={}
    for r in rows:
        if 'event' in r: events.setdefault(r['tick']//30,[]).append(r)
    samples=[]
    for a,b in zip(states,states[1:]):
        if b['tick']-a['tick']!=30 or a['life_state']!=0 or b['life_state']!=0: continue
        dx,dy=b['x']-a['x'],b['y']-a['y']; distance=np.hypot(dx,dy)
        if distance>550:continue # Teleports/large discontinuities are not movement clicks.
        action=0 if distance<25 else 1+int(np.floor((np.arctan2(dy,dx)+np.pi/8)%(2*np.pi)/(np.pi/4)))
        source='inferred_displacement' if action else 'inferred_stationary'
        future=events.get(a['tick']//30,[])+events.get(b['tick']//30,[])
        future=[e for e in future if a['tick']<e['tick']<=b['tick']]
        if any(e['event']=='attack_activity_proxy' for e in future):action=9;source='damage_activity_proxy'
        casts=[e for e in future if e['event']=='cast' and e['ability'] in CASTS]
        if casts: action=CASTS[casts[0]['ability']];source='recorded_cast_event'
        x=np.zeros(OBS_SIZE,dtype=np.float32)
        x[:5]=[a['x']/8192,a['y']/8192,a['hp']/max(1,a['max_hp']),a['mana']/max(1,a['max_mana']),a['level']/30]
        samples.append((a['tick'],x,action,source))
    if len(samples)>limit:
        samples=[samples[i] for i in np.linspace(0,len(samples)-1,limit,dtype=int)]
    return samples

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--per-match',type=int,default=600)
    parser.add_argument('--output',default='results/sf_replay');args=parser.parse_args()
    if args.per_match<50:raise ValueError('At least 50 samples per match')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(Path('data/replays/sf_manifest.json').read_text())
    w,sensory,motor,graph=load_full();brain=FullReservoir(w,sensory,motor,input_size=OBS_SIZE)
    datasets=[];excluded=[];provenance=[]
    for match in manifest['matches']:
        path=Path('data/replays/parsed')/f"{match['match_id']}.jsonl"
        rows=[json.loads(s) for s in path.read_text().splitlines()]
        if not match.get('player') or sum('event' not in r for r in rows)<1000:
            excluded.append(dict(match_id=match['match_id'],reason='Unnamed player or insufficient selected-hero state coverage'));continue
        samples=examples(rows,args.per_match)
        brain.reset();features=[];started=time.time()
        print(f"Encoding {match['match_id']} ({match['player']}): {len(samples)} samples, {match['split']}",flush=True)
        for i,(_,x,_,_) in enumerate(samples):
            features.append(brain.features(x))
            if i and i%200==0:print(f'  {i}/{len(samples)} encoded',flush=True)
        datasets.append((match['split'],np.array(features),np.array([s[2] for s in samples])))
        provenance.append(dict(match_id=match['match_id'],player=match['player'],split=match['split'],samples=len(samples),
            parsed_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            labels={name:sum(s[3]==name for s in samples) for name in {s[3] for s in samples}},seconds=time.time()-started))
    train=np.concatenate([f for split,f,y in datasets if split=='train'])
    labels=np.concatenate([y for split,f,y in datasets if split=='train'])
    scale=np.maximum(np.std(train,axis=0),1e-5);scale[-1]=1
    x=train/scale;counts=np.bincount(labels,minlength=ACTION_COUNT)
    sample_weight=1/np.sqrt(np.maximum(1,counts[labels]));sample_weight/=sample_weight.mean()
    def objective(flat):
        theta=flat.reshape(x.shape[1],ACTION_COUNT);logits=x@theta
        lp=logits-logsumexp(logits,axis=1,keepdims=True)
        loss=-np.mean(lp[np.arange(len(labels)),labels]*sample_weight)+.001*np.sum(theta[:-1]**2)
        p=np.exp(lp);p[np.arange(len(labels)),labels]-=1;p*=sample_weight[:,None]/len(labels)
        grad=x.T@p;grad[:-1]+=.002*theta[:-1]
        return loss,grad.ravel()
    fit=minimize(objective,np.zeros(x.shape[1]*ACTION_COUNT),jac=True,method='L-BFGS-B',options={'maxiter':500})
    decoder=fit.x.reshape(x.shape[1],ACTION_COUNT)/scale[:,None]
    np.savez_compressed(out/'policy.npz',decoder=decoder,self_fields=np.array(SELF_FIELDS),input_size=OBS_SIZE,action_count=ACTION_COUNT)
    majority=int(np.argmax(counts));metrics={}
    for split in ('train','validation','test'):
        f=np.concatenate([f for s,f,y in datasets if s==split]);y=np.concatenate([y for s,f,y in datasets if s==split])
        pred=np.argmax(f@decoder,axis=1)
        metrics[split]=dict(samples=len(y),accuracy=float(np.mean(pred==y)),majority_accuracy=float(np.mean(y==majority)),
            balanced_accuracy=float(np.mean([np.mean(pred[y==c]==c) for c in np.unique(y)])),
            class_counts=np.bincount(y,minlength=ACTION_COUNT).tolist(),
            zero_graph_accuracy=float(np.mean(np.argmax(decoder[-1])==y)))
    report=dict(status='Initial own-state pro-SF activity imitation; not a full-match competent policy',neurons=brain.n,
        optimizer_converged=bool(fit.success),optimizer_message=str(fit.message),metrics=metrics,matches=provenance,excluded=excluded,
        limitations=['Only own position, HP, mana and level; no enemy perception in this checkpoint',
        'Movement is inferred displacement, not exact clicks; damage activity is not attack-order timing',
        'Uniform subsampling across matches compresses time for recurrent state; no biological timing claim',
        'Fixed anatomical recurrence; engineered readout trained with supervised optimization',
        'Independent matches held out; small dataset and no rank inference'])
    (out/'metrics.json').write_text(json.dumps(report,indent=2));print(json.dumps(metrics,indent=2),flush=True)

if __name__=='__main__':main()
