"""Delayed-cue memory diagnostic; explicitly not a Dota performance benchmark."""
import json
from pathlib import Path
import torch
from fruit_fly_dota.recurrent import RecurrentPolicy

torch.manual_seed(9);p=RecurrentPolicy(64,2);opt=torch.optim.Adam(p.parameters(),lr=.003)
mask=torch.ones(64,2,dtype=torch.bool)
for epoch in range(150):
    labels=torch.randint(0,2,(64,));h=torch.zeros(64,64)
    opt.zero_grad()
    for t in range(8):
        x=torch.zeros(64,64)
        if t==0:x[:,0]=labels*2.-1.
        dist,_,h=p(x,h,mask)
    loss=-dist.log_prob(labels).mean();loss.backward();opt.step()
labels=torch.randint(0,2,(512,));h=torch.zeros(512,64);mask=torch.ones(512,2,dtype=torch.bool)
with torch.no_grad():
    for t in range(8):
        x=torch.zeros(512,64)
        if t==0:x[:,0]=labels*2.-1.
        dist,_,h=p(x,h,mask)
    accuracy=(dist.probs.argmax(-1)==labels).float().mean().item()
    no_memory,_,_=p(torch.zeros(512,64),torch.zeros(512,64),mask)
    reset_accuracy=(no_memory.probs.argmax(-1)==labels).float().mean().item()
report=dict(task='Synthetic cue followed by seven blank observations; not Dota',accuracy=accuracy,reset_memory_accuracy=reset_accuracy,passes=accuracy>.95 and reset_accuracy<.6)
Path('results/recurrent').mkdir(parents=True,exist_ok=True);Path('results/recurrent/memory_diagnostic.json').write_text(json.dumps(report,indent=2));print(report)
if not report['passes']:raise SystemExit(1)
