# Initial results

All percentages refer to 200 toy lane episodes, not Dota matches.

| Run | Cloned | RL candidate | Selected | Graph lesion | 95% interval (selected) |
|---|---:|---:|---:|---:|---|
| seed0 | 97.5% | 96.0% | 97.5% | 16.5% | 94.3–98.9% |
| seed1 | 93.0% | 89.5% | 93.0% | 0.0% | 88.6–95.8% |
| seed2 | 96.0% | 88.0% | 96.0% | 0.0% | 92.3–98.0% |
| shuffle | 97.5% | 96.5% | 97.5% | 0.0% | 94.3–98.9% |
| zero | 0.0% | 0.0% | 0.0% | 0.0% | 0.0–1.9% |
| reset | 98.5% | 98.0% | 98.5% | 16.5% | 95.7–99.5% |
| engineered | 88.5% | 89.0% | 89.0% | 0.0% | 83.9–92.6% |

Random: 17.5%; scripted teacher: 100%; untrained policies: 0%.

No demonstrated fly-specific topology or memory benefit. Shuffled wiring matches seed 0, and state reset performs similarly. These are initial controls with limited seeds, not equivalence tests.

Only the engineered-memory run accepted RL on validation; all other selected checkpoints retain cloning weights. Nonzero-graph cloning fits reached the fixed 250-iteration limit. See each metrics.json for fit status, validation scores, RL rewards and full episode records.

Default Fly Purity: 42/100 (subjective rubric, 256-neuron coverage). Dota rank: uncalibrated/null. No Dota engine run occurred.
