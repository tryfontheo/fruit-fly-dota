"""Explicit append-only migration; preserves previous weights and decoder columns."""
import argparse
from pathlib import Path
import numpy as np

def migrate(source,destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('Destination already exists; refusing to overwrite learning')
    with np.load(source,allow_pickle=False) as old:
        if int(old['input_size'])!=33 or int(old['action_count'])!=26:raise ValueError('Expected 33-input/26-action checkpoint')
        values={k:old[k].copy() for k in old.files}
    for name in ('weights','decoder'):
        if values[name].shape!=(65,26) or not np.isfinite(values[name]).all():raise ValueError('Invalid old matrices')
    values['weights']=np.column_stack((values['weights'],np.zeros((65,13))))
    extra=np.random.default_rng(7).normal(0,1,(65,13));extra[-1]=0
    values['decoder']=np.column_stack((values['decoder'],extra))
    values.update(input_size=46,action_count=39,migration='v3-to-v4-guide-items-preserved-first-33-inputs',source_checkpoint=str(source))
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as f:np.savez_compressed(f,**values)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('destination');a=p.parse_args();migrate(a.source,a.destination)
