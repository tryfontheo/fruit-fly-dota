"""Summarize actual outcomes; policy updates alone are not a skill metric."""
import json,collections,math
from pathlib import Path
import numpy as np

groups={}
for line in Path('work/shared-v6.jsonl').open():
    try:r=json.loads(line)
    except json.JSONDecodeError:continue
    s=groups.setdefault(r['session'],dict(n=0,rewards=collections.Counter(),near_base=0,dt=[],bad=0,version=0,actions=collections.Counter(),farm=0,xp=0,deaths=0,tp_healthy=0,minutes=0,agents=set(),reward_versions=set()))
    o=r['obs'];s['n']+=1;s['rewards'].update(r.get('reward_components',{}))
    v=r.get('reward_version','unknown');s['reward_versions'].add(v)
    components=r.get('reward_components',{})
    multiplier=2 if v=='lane-v5-farming' else 1
    s['farm']+=(components.get('last_hit',0)+components.get('jungle_last_hit',0))/multiplier
    s['xp']+=components.get('experience',0)/(.002 if multiplier==2 else .001)
    s['deaths']+=int(components.get('death',0)<0)
    s['actions'][r['action']]+=1;s['agents'].add(r['agent'])
    s['tp_healthy']+=r['action']==52 and o[2]>=.9
    s['minutes']=max(s['minutes'],o[7]*120)
    # Approximate location diagnostic, not engine fountain bounds.
    s['near_base']+=min(math.hypot(o[0]*8192+6700,o[1]*8192+6700),math.hypot(o[0]*8192-6800,o[1]*8192-6500))<1600
    s['dt'].append(r.get('dt',0));s['bad']+=not r.get('previous_applied',True);s['version']=r.get('policy_version',0)
report=[]
for session,s in list(groups.items())[-3:]:
    report.append(dict(session=session,decisions=s['n'],approximate_near_either_base_fraction=s['near_base']/s['n'],
        reward_totals=dict(s['rewards']),game_seconds_between_decisions_p95=float(np.percentile(s['dt'],95)),
        rejected_fraction=s['bad']/s['n'],policy_updates=s['version'],game_minutes=s['minutes'],
        reward_versions=sorted(s['reward_versions']),farm_kills=s['farm'],xp_gained=s['xp'],death_feedback_packets=s['deaths'],
        farm_kills_per_hero_minute=s['farm']/max(1,s['minutes']*len(s['agents'])),
        tp_home_choices=s['actions'][52],tp_home_choices_above_90_percent_hp=s['tp_healthy'],
        most_common_actions=s['actions'].most_common(8)))
print(json.dumps(report,indent=2))
