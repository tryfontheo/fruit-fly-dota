# fruit-fly-dota

A local **connectome-derived agent research project**, targeting full real Dota
matches in isolated Workshop Tools games. We have a trained small toy-lane
baseline, a running **176,422-neuron MaleCNS sparse model**, and a real-map
integration with a verified live movement round trip. Full-match competence is not established.
This is connectivity-based rate simulation, not validated full-brain physiology.

## Full model and real Dota

The main model uses the entire curated MaleCNS v1.0 Neuron selection: 176,422
nodes and 25,862,574 directed anatomical pairs. The approximately 166k headline
does not exactly match this explicit selection. See [full model](docs/FULL_MODEL.md)
for provenance, counts, omitted biology and the CPU benchmark.

[Real Dota setup](dota/README.md) uses the standard Dota map inside an isolated
addon. Visible telemetry passes to the full sparse network on localhost; a
readout requests compass movement, attacks or Lina spells. The live policy is
**untrained**. The old toy checkpoint is not presented as a real-game policy.
No public/ranked matchmaking is implemented. Items, leveling decisions, teammates,
objectives, real-game imitation and full-match RL remain upcoming milestones.

On September 13 the full graph received real observations and issued movement
orders in Dota build 25265195; positions changed and `fly_stop` stopped new orders.
See [engine smoke-test evidence](results/live_smoke/summary.json). Attack/spell
impacts and learned real-game behavior are **not yet verified**.

## What works

- A reproducible 256-neuron induced subgraph from a published FlyWire v783
  derivative: **5,016 directed pairs, 199,069 summed synaptic contacts**. Source
  commit, SHA-256, original IDs and extraction method are recorded.
- A leaky recurrent signed-rate model. Observations stimulate one population;
  only a separate population feeds the policy. No observation/action skip path.
- A four-action lane: wait, left, right, attack. Seeded starting positions and
  creep health, attack range, windup, cooldown, background damage and last-hit
  attribution. These are invented task parameters, not Dota's actual rules.
- Behavior cloning from a labeled **synthetic teacher**, followed by a small
  policy-gradient RL pass. The trainable component is an engineered linear
  action readout; biological recurrent weights stay fixed.
- Native recurrent-state memory, state-reset and explicit previous-observation
  memory ablations. No LSTM, transformer, or hidden tactical planner.
- Held-out evaluation, independent learning seeds, disconnected/shuffled wiring
  controls, model checkpoints, a disclosed Fly Purity rubric and a Lua exporter.
- Replay interchange validation, a small-model Lua exporter, and a full-model
  local HTTP adapter for Workshop Tools.

## Initial results (September 13, 2026)

Each evaluation uses the same 200 held-out toy episodes. Three intact runs
achieved **97.5%, 93.0%, and 96.0%** last hits. Random actions achieved **17.5%**;
the engineered demonstration policy achieved **100%**. Disconnecting seed 0's
trained graph reduced it to **16.5%**, and training with disconnected wiring
achieved **0%**.

**The shuffled graph also achieved 97.5%. There is no demonstrated advantage
from fly-specific topology.** Resetting recurrent state each observation achieved
98.5%; this task does not establish a benefit from memory. A previous-observation
memory ablation achieved 89.0%. The default RL pass failed to improve validation
reward and was rejected; the saved default remains behavior-cloned. The memory
ablation's RL candidate was accepted, but this is not robust evidence of RL gains.

The nonzero-graph fits hit the declared 250-iteration optimization budget; they
are usable checkpoints, **not converged optima**. Full episode records and Wilson
intervals are in `results/*/metrics.json`; see [results summary](results/SUMMARY.md).
No Dota MMR/rank is inferred. Previous conversation rank guesses lacked evidence.

## Run locally (PowerShell, from this directory)

The local `.venv` is already installed and the processed dataset is included.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m fruit_fly_dota.cli run --output results\my-run
.\.venv\Scripts\python.exe -m fruit_fly_dota.cli run --ablation shuffle --output results\my-shuffle
.\.venv\Scripts\python.exe -m fruit_fly_dota.cli run --memory reset --output results\my-reset
.\.venv\Scripts\python.exe -m fruit_fly_dota.cli run --memory engineered --output results\my-memory
.\.venv\Scripts\python.exe -m fruit_fly_dota.export_lua --policy results\seed0
```

For a fresh checkout: `powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1`.
This creates a virtual environment, installs pinned dependencies, downloads the
~101 MB upstream parquet, checks its pinned hash, recreates the subset and runs
tests. An internet connection is only needed for setup. There are no paid APIs.
Use Python 3.13 on Windows to reproduce the pinned environment tested here;
`pyproject.toml` permits Python 3.11+ but other platforms/versions are untested.
The reference runs use CPU NumPy/SciPy; the available RTX 5090 is not required.

## Architecture and honesty boundaries

```text
Player-visible structured observation [engineered perception]
  -> fixed random population encoder [engineered, no anatomical mapping]
  -> actual FlyWire subgraph + phenomenological leaky dynamics [connectivity-derived]
  -> separate downstream population
  -> trained linear softmax readout [engineered learning]
  -> wait / move left / move right / attack [engineered action abstraction]
```

The native temporal state resets between episodes. Learning across episodes lives
in the readout weights. No learned memories from the original animal survive in a
connectivity dataset. Synaptic plasticity, spiking, measured time constants,
neuromodulation, realistic senses and an actual body are not implemented here.

Fly Purity is **42/100 under our subjective version-0.1 rubric**, alongside tiny
coverage and explicit scaffolding. It is not a scientific measurement or a
percentage of intelligence supplied by a fly. See [methodology](docs/METHODOLOGY.md).

## Research and next milestone

[Research audit](docs/RESEARCH.md) separates the supplied Instagram/FPS claims
from verified connectomics, FlyGym/NeuroMechFly and published simulation work.
The supplied clips' code and Masters claim could not be authenticated.

[Dota integration](dota/README.md) documents the chosen Workshop Tools route,
what was inspected locally, adapter limitations and an engine-test checklist.
No public/ranked automation is included. No installed Dota files were modified.

Next: enable Workshop Tools, build the isolated single-creep fixture, measure
actual attack timing, validate Lua/Python parity on recorded telemetry, and train
against that environment. Keep the toy simulator as a regression harness.
Then add fog/delayed-cue tasks to test memory and anatomically annotated sensory
and descending populations to replace arbitrary population wiring.

Replay imitation begins with [the data contract](docs/REPLAYS.md). No `.dem` or
YouTube recording was supplied or processed. Never equate spectator state with
player-visible information, or state changes with recorded player orders.

## Files

`src/fruit_fly_dota/`: connectome, observation, action, neural, learning, evaluation,
replay interchange and Lua export modules. `data/processed/`: measured subset and
provenance. `results/`: seven reproducible experiments and checkpoints.
`dota/`: staged engine integration. `tests/`: data integrity, neural causality,
memory, lane semantics, replay contract and Python/Lua parity checks.

Code: MIT, see [LICENSE](LICENSE). Upstream attribution and license are retained
in `data/raw/UPSTREAM_LICENSE`; biological data attribution is in the manifest and
research notes. The project is not affiliated with Valve or the research teams.
