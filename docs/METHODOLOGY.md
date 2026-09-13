# Methodology and limitations

## Biological substrate

The pinned Shiu repository's FlyWire v783 parquet contains 15,091,983 rows. We
rank neurons by summed incident synapse count, retain 256 (stable ID tie-break),
and retain all directed edges between them. Original IDs, rows, signed counts and
checksums are kept. This chooses strongly connected hubs for a small compute
test, not a known sensory/motor circuit. Selection is independent of game reward.
No claim is made that this subset is representative of the fly brain.

Matrix entry `W[post,pre]` sums upstream signed synapse counts. We inherit
upstream neurotransmitter sign assumptions without re-estimating them. Rows are
scaled to absolute sum <=0.9. This engineering normalization preserves nonzero
support, direction and sign, but changes effective strength and physiology.

## Model and scaffolding

For each observation: four updates `h <- .25*h + .75*tanh(W*h + B*x + bias)`.
The coefficients have no fitted biological units. Signed tanh activity is not a
literal nonnegative firing rate. This is a connectivity-constrained reservoir,
not the Shiu LIF implementation. First 128 units receive a fixed random encoder;
only last 128 units reach the readout. This forces an edge-mediated path. The
encoder and population assignment are artificial and are not anatomical senses
or motor neurons. The final bias can issue constant actions even when silenced.

Six observation fields: hero position, visible target position, visible target
health, own cooldown, own windup and visibility. Normalization is engineered.
No teacher decision, future health, damage schedule, or direct observation feature
is fed into the policy readout. Structured telemetry is powerful scaffolding.

Four actions form an artificial action vocabulary. In the toy task no target
selection or aiming is needed: there is exactly one creep. Movement and attack
timing must be learned. Wait continues an in-progress attack; movement cancels
windup. Background damage is deterministic within a seeded episode. There are no
other heroes, towers, abilities, items, fog, denies, armor or projectiles.

## Learning

300 synthetic demonstration episodes with 12% random executed actions provide
off-teacher examples. The label remains the scripted teacher's desired action.
This is not human replay imitation. Multinomial logistic regression fits only
129x4 readout parameters with L2 penalty 1e-4, feature scaling and L-BFGS-B capped
at 250 iterations. Fit status is preserved; the nonzero-graph fits hit the cap.
Neural connectivity and the encoder never learn. Success means an engineered
readout learned to use a graph-derived representation.

300 episodic REINFORCE trials then update that same readout (discount .99,
running scalar baseline, learning rate .002, gradient norm cap 5). No teacher is
queried in RL. Accept only if mean reward improves on separate validation seeds.
Retain both candidate and selected-policy test metrics, including negative results.
RL performance is not expected to improve reliably after near-perfect imitation.

Default training task seeds: 1000..1299; RL: 100000..100299; validation:
800000..800099; test: 900000..900199. Other learning seeds shift the training/RL
ranges and encoder. The same test episodes across runs allow paired comparisons;
do not treat the three runs as 600 independent environment tests. These intervals
must remain disjoint when changing episode counts or accepting external data.
Future experiments should preregister settings and reserve new test seeds before
tuning; this initial test set has now been inspected.

## Memory

Default: recurrent state persists across observations, reset at episode boundary.
`reset`: reset before every observation, retaining within-observation propagation.
`engineered`: concatenate the previous observation before encoding; explicit
nonbiological storage and a larger encoder. It is not a clean capacity-matched
comparison, and results are not a verdict on whether memory generally helps.
The task is essentially fully observed; no memory benefit is established.
Next add delayed sensory cues/temporary occlusion and measure performance against
cue delay, recurrence lesions and state resets. Fit retention curves, not a claim
of remembering for seconds/minutes based on unspecified simulation time.
Biologically motivated eligibility traces and dopamine-gated plasticity are future
work, not implemented biological learning.

## Evaluation

Primary: fraction of held-out episodes ending with agent-attributed last hit.
Also record reward, invalid attack attempts, attacks and episode steps. Report
Wilson 95% intervals across episodes, learning-seed variation and full records.
Disconnected fixed-readout lesions test reliance on the graph; retrained shuffled
controls test whether exact fly wiring provides an advantage. Shuffling preserves
each source's outgoing weight multiset/sign before normalization, not destination
degree, motifs, anatomical meaning or exact spectrum. Add degree-preserving rewires,
matched random reservoirs and direct-observation learners in stronger studies.

Rank-like evaluation is a future **local benchmark ladder**, not Dota MMR:
stationary target -> moving lane -> passive opponent -> scripted hostile opponent
-> private 1v1. For each tier report last hits/minute, contested last-hit fraction,
denies, deaths, net-worth difference, win rate, action rate and inference latency.
Fit an internal Elo only after repeated pairwise matches against fixed versions
of opponents. A public rank mapping would need independent human calibration and
cannot be inferred from this toy task. Current `dota_rank` is null.

## Fly Purity v0.1

An intentionally subjective ledger, not a validated scalar measure of intelligence.
Report all components, coverage, learning location and lesion results with it.

| Component | Maximum | Current | Rationale |
|---|---:|---:|---|
| Anatomical connectivity | 30 | 30 | Edges come from measured subset; coverage separately disclosed |
| Physiology | 20 | 2 | Phenomenological leak only, no calibrated spikes |
| Anatomical input/output | 15 | 0 | Arbitrary population encoding/decoding |
| Biological learning | 20 | 0 | Artificial readout optimization, no plasticity |
| Intrinsic memory | 10 | 5 | Leaky recurrence, no validated timescale |
| No policy bypass | 5 | 5 | Inputs reach readout only through graph |

Default 42/100. Shuffling/disconnecting removes anatomical points; external memory
or resetting removes intrinsic-memory points. The score can be gamed: displaying
many neurons, keeping irrelevant edges, or putting intelligence in telemetry can
inflate appearances. Coverage and causal interventions are more informative.
