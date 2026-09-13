"""Extract only addon telemetry, never copy raw account-bearing Dota console logs."""
import json
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parents[1]
records=[json.loads(line) for line in (root/'work/live.jsonl').read_text().splitlines()]
console=Path('C:/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota/console.log').read_text(errors='replace')
orders=[]
for line in console.splitlines():
    if '[VScript] FLY_ORDER\t' in line:
        s,a,x,y=line.split('FLY_ORDER\t',1)[1].split()
        orders.append(dict(seq=int(s),action=int(a),x=float(x),y=float(y)))
assert records and orders
byseq={r['seq']:r for r in records}
assert all(o['seq'] in byseq and byseq[o['seq']]['action']==o['action'] for o in orders)
positions=np.array([[o['x'],o['y']] for o in orders])
result=dict(status='Verified real-map observation → full connectome → movement order round trip; untrained',
    date='2026-09-13',dota_build=25265195,neurons=176422,
    observations=len(records),issued_orders=len(orders),
    observed_order_actions=sorted({o['action'] for o in orders}),
    first_position=positions[0].tolist(),last_position=positions[-1].tolist(),
    displacement=float(np.linalg.norm(positions[-1]-positions[0])),
    mean_decision_ms=float(np.mean([r['decision_ms'] for r in records])),
    p95_decision_ms=float(np.percentile([r['decision_ms'] for r in records],95)),
    stop_recorded=console.rfind('FLY_STOP')>console.rfind('FLY_ORDER'),
    limitations=['No attack/spell impact verified','No learning or full-match performance measured',
                 'Plain addon hero; no other hero bots','Movement partly determined by engineered exploration and legal mask'])
out=root/'results/live_smoke'; out.mkdir(exist_ok=True)
(out/'summary.json').write_text(json.dumps(result,indent=2))
(out/'orders.json').write_text(json.dumps(orders,indent=2))
(out/'observations.jsonl').write_text('\n'.join(json.dumps(r) for r in records)+'\n')
print(json.dumps(result,indent=2))
