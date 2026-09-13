# Full MaleCNS model

The main experiment now uses the curated Neuron population in MaleCNS v1.0.
The 166k figure is the release's approximate headline brain count; our explicit
neuPrint selection returns **176,422 neurons**, including annotated brain and
ventral nerve cord populations. We do not pad a smaller graph to a desired count.
The manifest records the exact query, selection hash, sources and processing.

There are **25,862,574 directed anatomical pairs**, representing **125,024,864
synapses** after the published confidence filter. All selected nodes are retained.
The sparse rate model keeps **24,614,339 nonzero fast-sign connections**:
acetylcholine is positive, GABA/glutamate negative, other/unknown signs zero.
This omits receptor details and neuromodulation. Connectivity is biological;
the dynamics are an engineered approximation, not a validated physiological
full-brain simulation or a claim of fly consciousness.

Signals enter 17,336 annotated sensory neurons through a fixed random encoder.
Only 2,129 descending/motor neurons feed 64 fixed mean pools and a linear
readout. Sensory and readout populations do not overlap. There is no direct
observation-to-readout shortcut. Four recurrent substeps retain native network
state between decisions; reset-state and engineered-memory comparisons remain
required. Zeroing connections removes the downstream input-dependent signal.

## Reproduce

From the repository environment:

```powershell
python -m fruit_fly_dota.malecns
python scripts/benchmark_full.py
python -m fruit_fly_dota.live
```

The builder downloads roughly 1.1 GB of versioned public data and queries the
public neuPrint endpoint read-only. Allow several GB of RAM and disk for building.
Raw and derived large arrays are excluded from Git; the manifest is committed.
Data attribution and CC BY 4.0 provenance are recorded in that manifest.

The local CPU benchmark measured 41.9 ms mean and 44.3 ms p95 for a six-input,
four-substep decision. The sparse effective matrix occupies about 198 MB.
This is a throughput test, not evidence of Dota competence. Live telemetry uses
16 inputs and needs its own latency measurements under game load.

## Scientific status

The existing trained 256-neuron toy experiment remains a debugging baseline.
Its decoder cannot be reused for this different graph and observation schema.
The full live decoder is explicitly **untrained**, with stochastic exploration.
There is no full-model learning result, full-match win rate, or rank estimate yet.
The old 42/100 Fly Purity score describes only the small toy experiment; do not
carry it forward as a measured score for this model. Report anatomical coverage,
signed-edge coverage, engineered encoder/pooling/target selection, learning method,
memory intervention and lesion results separately before assigning a new score.

Sources: [MaleCNS downloads](https://male-cns.janelia.org/download/),
[official release](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/).
