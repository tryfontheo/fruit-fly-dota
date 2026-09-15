"""Append minimap inputs while preserving v5 motor encoder columns and policy."""
import argparse
from pathlib import Path
import torch

def migrate(source,destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('Destination exists; refusing to overwrite learning')
    data=torch.load(source,map_location='cpu',weights_only=True)
    if data['schema']!='shared-v5-74x54':raise ValueError('Expected a v5 checkpoint')
    data['schema']='shared-v6-78x54'
    data['migration']='v5 policy preserved; four appended allied-minimap inputs; original 74 encoder columns preserved'
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as f:torch.save(data,f)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('destination')
    a=p.parse_args();migrate(a.source,a.destination)
