"""Recover an interrupted seed-zero online run from its complete action log.

Requires the identical base policy, model and initial learner. Refuses to save
if reproduced actions differ. This is recovery, not a new evaluation rollout.
"""
import argparse,json
from pathlib import Path
import numpy as np
from fruit_fly_dota.live import Controller,OBS_SIZE
from fruit_fly_dota.full_neural import FullReservoir
from fruit_fly_dota.malecns import load_full

p=argparse.ArgumentParser();p.add_argument('--log',required=True)
p.add_argument('--policy',required=True);p.add_argument('--output',required=True)
args=p.parse_args()
w,s,m,_=load_full();c=Controller(FullReservoir(w,s,m,input_size=OBS_SIZE),policy=args.policy,learn=True)
rows=[json.loads(line) for line in Path(args.log).read_text().splitlines()]
if not rows or rows[0]['seq']!=0:raise ValueError('Requires complete initial run')
for row in rows:
    result=c.step(row)
    if result['action']!=row['action']:raise ValueError(f"Action mismatch at {row['seq']}")
np.savez_compressed(args.output,weights=c.learner.weights,total_reward=c.learner.total_reward,updates=c.learner.updates)
print(f'Recovered {len(rows)} decisions; {c.learner.updates} updates; reward {c.learner.total_reward:.3f}')
