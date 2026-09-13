"""Official MaleCNS v1.0 full Neuron-label graph; no synapse-count threshold."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen, urlretrieve
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.ipc as ipc
from scipy.sparse import csr_matrix, save_npz, load_npz
from .connectome import sha256

BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/"
FILES = {
    "annotations.feather":"body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "neurotransmitters.feather":"body-neurotransmitters-male-cns-v1.0.feather",
    "connections.feather":"connectome-weights-male-cns-v1.0-minconf-0.5.feather",
}
QUERY = "MATCH (n:Neuron) RETURN n.bodyId AS bodyId ORDER BY bodyId"
API = "https://neuprint.janelia.org/api/custom/custom"

def download(root):
    raw=Path(root)/"raw"; raw.mkdir(parents=True,exist_ok=True)
    for local,remote in FILES.items():
        dest=raw/local
        if not dest.exists():
            print(f"Downloading {remote}",flush=True)
            tmp=dest.with_suffix(".partial")
            urlretrieve(BASE+remote,tmp)
            tmp.replace(dest)
    if not (raw/"neuron_ids.json").exists():
        request=Request(API,data=json.dumps(dict(dataset="male-cns:v1.0",cypher=QUERY)).encode(),
            headers={"Content-Type":"application/json"})
        with urlopen(request,timeout=120) as r:
            (raw/"neuron_ids.json").write_bytes(r.read())

def build(root="data/malecns"):
    root=Path(root); download(root)
    raw=root/"raw"; out=root/"processed"; out.mkdir(parents=True,exist_ok=True)
    response=json.loads((raw/"neuron_ids.json").read_text())
    ids=np.array([row[0] for row in response["data"]],dtype=np.int64)
    if len(ids)<160000 or len(np.unique(ids))!=len(ids) or np.any(np.diff(ids)<=0):
        raise ValueError("Unexpected full MaleCNS neuron selection")
    ann=pd.read_feather(raw/"annotations.feather").set_index("bodyId").reindex(ids)
    nt=pd.read_feather(raw/"neurotransmitters.feather").set_index("body").reindex(ids)
    # Explicit sign convention, not receptor-resolved physiology. Unknown and
    # modulatory transmitters contribute zero fast current but remain in anatomy.
    transmitter=nt.consensus_nt.fillna(nt.celltype_predicted_nt).fillna(nt.predicted_nt)
    signs=transmitter.map({"acetylcholine":1,"gaba":-1,"glutamate":-1}).fillna(0).to_numpy(dtype=np.float32)
    pre_chunks,post_chunks,weight_chunks=[],[],[]
    scanned=0
    with pa.memory_map(str(raw/"connections.feather"),"r") as source:
        reader=ipc.open_file(source)
        value_set=pa.array(ids)
        for i in range(reader.num_record_batches):
            batch=reader.get_batch(i)
            pre=pc.fill_null(pc.index_in(batch.column("body_pre"),value_set=value_set),-1).to_numpy()
            post=pc.fill_null(pc.index_in(batch.column("body_post"),value_set=value_set),-1).to_numpy()
            weights=batch.column("weight").to_numpy()
            keep=(pre>=0)&(post>=0)
            pre_chunks.append(pre[keep].astype(np.int32))
            post_chunks.append(post[keep].astype(np.int32))
            weight_chunks.append(weights[keep].astype(np.float32))
            scanned+=batch.num_rows
            if i%200==0: print(f"Scanned {scanned:,} connection rows",flush=True)
    pre=np.concatenate(pre_chunks); post=np.concatenate(post_chunks); counts=np.concatenate(weight_chunks)
    if not np.isfinite(counts).all() or np.any(counts<=0): raise ValueError("Invalid weights")
    anatomy=csr_matrix((counts,(post,pre)),shape=(len(ids),len(ids)))
    anatomy.sum_duplicates(); anatomy.sort_indices()
    save_npz(out/"anatomy.npz",anatomy)
    effective=anatomy.copy(); effective.data *= signs[effective.indices]
    effective.eliminate_zeros()
    save_npz(out/"weights.npz",effective)
    np.save(out/"neuron_ids.npy",ids)
    superclasses=ann.superclass.fillna("unannotated").to_numpy(dtype=str)
    sensory=np.flatnonzero(np.isin(superclasses,["ol_sensory","cb_sensory","vnc_sensory"]))
    motor=np.flatnonzero(np.isin(superclasses,["descending_neuron","cb_motor","vnc_motor"]))
    np.savez(out/"populations.npz",sensory=sensory,motor=motor)
    summary=ann[["type","superclass","class","somaSide","status"]].copy()
    summary["transmitter"]=transmitter; summary["model_sign"]=signs
    summary.to_parquet(out/"annotations.parquet")
    manifest=dict(dataset="MaleCNS v1.0",created_utc=datetime.now(timezone.utc).isoformat(),
        selection="All entries labeled Neuron by neuPrint male-cns:v1.0; induced graph on those IDs",
        selection_query=QUERY,selection_endpoint=API,source_page="https://male-cns.janelia.org/download/",
        selected_neurons=len(ids),directed_pairs=int(anatomy.nnz),synapse_count=int(anatomy.sum()),
        effective_fast_pairs=int(effective.nnz),minimum_pair_synapses=1,upstream_synapse_confidence=.5,
        source_connection_rows=scanned,sensory_neurons=len(sensory),readout_neurons=len(motor),
        zero_fast_sign_neurons=int(np.count_nonzero(signs==0)),
        superclasses=pd.Series(superclasses).value_counts().to_dict(),
        sign_assumption="ACh +1; GABA/glutamate -1; other/unknown 0. No receptor model or modulation.",
        source_files={k:dict(url=BASE+v,sha256=sha256(raw/k)) for k,v in FILES.items()},
        selection_sha256=sha256(raw/"neuron_ids.json"),weights_sha256=sha256(out/"weights.npz"),
        anatomy_sha256=sha256(out/"anatomy.npz"),ids_sha256=sha256(out/"neuron_ids.npy"),
        populations_sha256=sha256(out/"populations.npz"),
        license="CC BY 4.0",attribution="FlyEM (HHMI Janelia), University of Cambridge, MRC LMB, Google Research; Berg et al., Cell 2026",
        limitations=["Full selected neuronal graph, not all segmentation fragments", "Not a validated full physiological brain simulation", "Population encoding and rate dynamics engineered", "Neuromodulation and unknown fast signs not simulated"])
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({k:manifest[k] for k in ["selected_neurons","directed_pairs","synapse_count","effective_fast_pairs","sensory_neurons","readout_neurons"]},indent=2))
    return manifest

def load_full(root="data/malecns"):
    root=Path(root)/"processed"; m=json.loads((root/"manifest.json").read_text())
    for name,key in [("weights.npz","weights_sha256"),("neuron_ids.npy","ids_sha256"),("populations.npz","populations_sha256")]:
        if sha256(root/name)!=m[key]: raise ValueError(f"MaleCNS checksum mismatch: {name}")
    w=load_npz(root/"weights.npz")
    if w.shape!=(m["selected_neurons"],)*2 or not np.isfinite(w.data).all(): raise ValueError("Invalid MaleCNS matrix")
    with np.load(root/"populations.npz",allow_pickle=False) as p:
        return w,p["sensory"].copy(),p["motor"].copy(),m

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--root",default="data/malecns")
    build(p.parse_args().root)
