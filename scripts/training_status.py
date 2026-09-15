"""Read-only local training health; does not require Codex or load the brain."""
import json,time
from pathlib import Path
from urllib.request import urlopen

try:
    with urlopen('http://127.0.0.1:8765/state',timeout=5) as response:
        state=json.load(response)
    age=time.time()-state.get('wall_time',0)
    print('Receiving game observations' if age<10 else 'Waiting for game observations')
    print('Active heroes:',state.get('active_agents',0))
    print('Policy updates:',state.get('policy_version',0))
    if state.get('wall_time'):print('Last observation: %.1f seconds ago'%age)
    print('Last parameter change:',state.get('ppo',{}).get('parameter_change','not measured yet'))
except Exception as error:
    print('Trainer unavailable:',error)
    print('Run Start-SelfPlay.cmd or Start-Training.cmd to resume.')
checkpoint=Path(__file__).resolve().parents[1]/'work/shared-v6.pt'
if checkpoint.exists():print('Checkpoint saved %.1f seconds ago'%(time.time()-checkpoint.stat().st_mtime))
print('Updates confirm training runs; they do not prove improved game skill.')
