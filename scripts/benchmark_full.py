"""No learning claim: full graph load, signal propagation, lesion and latency."""
import json
import time
from pathlib import Path
import numpy as np
from fruit_fly_dota.malecns import load_full
from fruit_fly_dota.full_neural import FullReservoir

w,sensory,motor,manifest=load_full()
brain=FullReservoir(w,sensory,motor)
rng=np.random.default_rng(2026)
observations=rng.uniform(-1,1,(25,6))
timings=[]; features=[]
for obs in observations:
    t=time.perf_counter(); features.append(brain.features(obs)); timings.append(time.perf_counter()-t)
result=dict(neurons=brain.n,anatomical_pairs=manifest["directed_pairs"],effective_pairs=brain.w.nnz,
    state_dtype=str(brain.state.dtype),substeps=brain.substeps,
    sparse_matrix_mb=(brain.w.data.nbytes+brain.w.indices.nbytes+brain.w.indptr.nbytes)/1e6,
    mean_decision_ms=float(np.mean(timings[2:])*1000),p95_decision_ms=float(np.percentile(timings[2:],95)*1000),
    downstream_feature_norm=float(np.linalg.norm(np.asarray(features)[:,:-1])),
    downstream_feature_variation=float(np.std(np.asarray(features)[:,:-1],axis=0).mean()),
    status="Full selected MaleCNS sparse rate inference only; no Dota skill measured")
brain.w.data[:]=0; brain.reset()
lesioned=np.array([brain.features(obs) for obs in observations])
result["zero_graph_downstream_norm"]=float(np.linalg.norm(lesioned[:,:-1]))
assert result["downstream_feature_norm"]>0 and result["zero_graph_downstream_norm"]==0
path=Path("results/full_model"); path.mkdir(parents=True,exist_ok=True)
(path/"benchmark.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
