"""Versioned real-data extraction. No synthetic fallback in the experiment."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlretrieve
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, save_npz, load_npz

REVISION = "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960"
SOURCE = f"https://raw.githubusercontent.com/philshiu/Drosophila_brain_model/{REVISION}/Connectivity_783.parquet"
SOURCE_SHA256 = "efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def prepare(root, size=256):
    root = Path(root)
    raw = root / "raw" / "Connectivity_783.parquet"
    raw.parent.mkdir(parents=True, exist_ok=True)
    if not raw.exists():
        urlretrieve(SOURCE, raw)
    if sha256(raw) != SOURCE_SHA256:
        raise ValueError("Pinned upstream connectivity checksum mismatch")
    frame = pd.read_parquet(raw)
    required = {"Presynaptic_ID", "Postsynaptic_ID", "Connectivity", "Excitatory x Connectivity"}
    if not required <= set(frame.columns):
        raise ValueError("Unexpected upstream schema")
    # Select top incident-weight neurons, then the induced directed subgraph.
    # Deliberately structural, NOT claimed to be a functional sensory/motor circuit.
    degree = frame.groupby("Presynaptic_ID").Connectivity.sum().add(
        frame.groupby("Postsynaptic_ID").Connectivity.sum(), fill_value=0)
    ids = degree.sort_index().sort_values(ascending=False, kind="stable").head(size).index.to_numpy(dtype=np.int64)
    sub = frame[frame.Presynaptic_ID.isin(ids) & frame.Postsynaptic_ID.isin(ids)]
    index = {int(v): i for i, v in enumerate(ids)}
    pre = sub.Presynaptic_ID.map(index).to_numpy()
    post = sub.Postsynaptic_ID.map(index).to_numpy()
    signed = sub["Excitatory x Connectivity"].to_numpy(dtype=float)
    w = csr_matrix((signed, (post, pre)), shape=(size, size))
    w.sum_duplicates()
    dest = root / "processed"
    dest.mkdir(parents=True, exist_ok=True)
    save_npz(dest / "weights.npz", w)
    np.save(dest / "neuron_ids.npy", ids)
    sub.to_csv(dest / "edges.csv", index=False)
    manifest = dict(source_url=SOURCE, upstream_revision=REVISION, dataset="FlyWire FAFB v783, Shiu repository derivative",
        source_sha256=sha256(raw), source_rows=len(frame), selected_neurons=len(ids), directed_pairs=w.nnz,
        synapse_count=int(sub.Connectivity.sum()), selection="Top incident synapse count, stable ID tie break; induced subgraph",
        weights_sha256=sha256(dest / "weights.npz"), ids_sha256=sha256(dest / "neuron_ids.npy"),
        limitations=["Connectivity and upstream inferred signs only", "No anatomical input/output annotation", "Not MaleCNS", "Not a whole brain", "Upstream table is a derivative, not raw EM data"],
        attribution="FlyWire Consortium; Dorkenwald et al. 2024; Shiu et al. 2024. See docs/RESEARCH.md and data/raw/UPSTREAM_LICENSE.")
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

def load(root):
    root = Path(root) / "processed"
    manifest = json.loads((root / "manifest.json").read_text())
    for file, key in [("weights.npz", "weights_sha256"), ("neuron_ids.npy", "ids_sha256")]:
        if sha256(root / file) != manifest[key]:
            raise ValueError(f"Connectome integrity failure: {file}")
    w = load_npz(root / "weights.npz")
    if w.shape != (manifest["selected_neurons"],) * 2 or not np.isfinite(w.data).all():
        raise ValueError("Invalid connectome")
    return w, manifest
