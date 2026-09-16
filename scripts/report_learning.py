"""Summarize actual outcomes; policy updates alone are not a skill metric."""
import json,collections,math
from pathlib import Path
import numpy as np

groups={}
for line in Path('work/shared-v6.jsonl').open():
    try:r=json.loads(line)
    except json.JSONDecodeError:continue
    s=groups.setdefault(r['session'],dict(n=0,rewards=collections.Counter(),near_base=0,dt=[],bad=0,version=0))
    o=r['obs'];s['n']+=1;s['rewards'].update(r.get('reward_components',{}))
    # Approximate location diagnostic, not engine fountain bounds.
    s['near_base']+=min(math.hypot(o[0]*8192+6700,o[1]*8192+6700),math.hypot(o[0]*8192-6800,o[1]*8192-6500))<1600
    s['dt'].append(r.get('dt',0));s['bad']+=not r.get('previous_applied',True);s['version']=r.get('policy_version',0)
report=[]
for session,s in list(groups.items())[-3:]:
    report.append(dict(session=session,decisions=s['n'],approximate_near_either_base_fraction=s['near_base']/s['n'],
        reward_totals=dict(s['rewards']),game_seconds_between_decisions_p95=float(np.percentile(s['dt'],95)),
        rejected_fraction=s['bad']/s['n'],policy_updates=s['version']))
print(json.dumps(report,indent=2))
