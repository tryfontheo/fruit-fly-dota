# Shared recurrent self-play

Run **Start-SelfPlay.cmd** for local 5v5, or **Start-Training.cmd** for lane practice.
If Dota is already open, load the fruit_fly_dota addon once. Watch
http://127.0.0.1:8765/ and select player 0–9. `fly_camera_follow 0` follows SF;
`fly_camera_free` releases the camera; `fly_stop` stops all agents.

Training runs locally without Codex credits or messages. It saves atomically every
100 decisions and at terminal results to `work/shared-v5.pt`, restoring weights
and optimizer on restart. Keep that file. Logs are `work/shared-v5.jsonl` and
`work/trainer.log`. The supervisor restarts failed Python workers after five
seconds. Dota crashes require relaunching. Keep the computer awake. Temporary
per-hero memory resets for new matches/processes; learned weights persist.

## Architecture

74 structured observations → 176,422-neuron MaleCNS connectivity-derived rate
dynamics → 64 motor features → engineered 64-unit GRU → 54 legal-masked actions.
There is no raw-observation bypass. Anatomical weights remain fixed; GRU, actor
and critic learn. This is not validated full-brain physiology or biological
dopamine. Each hero has independent neural/GRU state; all share policy weights,
not private fog observations. Recurrent PPO pools 256 transitions, uses 32-step
chunks and three epochs. Version checks reject stale transitions; failed orders
discard that stream's short rollout to avoid crediting unexecuted choices.

One match contains five SFs per team with normal deaths/respawns. Actual results
request +100 for winners, -100 for losers and a reload after 15 seconds. A
30-minute timeout is a draw with zero outcome bonus. Full-game completion/reload
still needs live verification. No extra game XP is granted. Practice resets
after 300 seconds or death; `fly_round_seconds 600` changes its length. Items and
levels persist between practice rounds, so those are not independent evaluations.

The protocol names environments, but this addon uses one local environment.
Eight to sixteen concurrent Dota processes and GPU acceleration are not implemented.
CPU graph processing is serial: a requested 0.1-second interval does not guarantee
10 Hz per hero or meaningful APM. Cast points/channeling are protected.

## Actions and scaffolding

54 choices cover wait, eight movement directions, four visible enemy target slots,
three razes, Frenzy (R), Requiem (Y), four skill upgrades, eight talents, seven
component purchases, eight guide items, five item activations, visible rune pickup,
stop, TP purchase and TP to base. These are game orders, not physical key presses.

Guide items: Power Treads, Mask of Madness, Dragon Lance, BKB, Silver Edge, Satanic,
Daedalus and Butterfly. Activations: MoM, BKB, Silver Edge, Satanic and Treads toggle.
The paid custom shop buys complete items at full listed price near base; component
assembly, courier delivery and inventory management are incomplete. There is no
scripted route, retreat, build order or tactical item-use priority. Legal masks,
structured inputs and target selection are engineered scaffolding.

Still missing: deliberate ally targeting/denies, arbitrary ground targeting,
wards, courier control, selling/rearranging items and other TP destinations.
Explicit last-seen fog records are not supplied; native activity and GRU retain
their own history. Cooldown/readiness coverage is partial.

## Evidence and limits

Five professional SF replays supply 1,800 training labels and separate 600-label
validation/test matches. IDs/hashes/metrics are in `results/recurrent/imitation.json`.
The initial parser supplies own position, HP, mana and level; other live fields
are zero. Movement/attack labels are inferred proxies, not recorded clicks. Only
14 labels are represented. This does not teach item/rune/team strategy.

Normalized features and 30 imitation epochs produced 28.83% test accuracy versus
21.50% majority baseline. Clearing memory scored 30.33%: no Dota memory benefit
is established. Zero graph features scored 21.50%, which does not prove fly
anatomy superiority. A separate synthetic delayed-cue test scored 100% with memory
versus 48.44% with memory cleared. That establishes a memory mechanism, not Dota
competence. See `scripts/train_recurrent_replays.py` and `check_recurrent_memory.py`.

The normalized candidate initializes the current local checkpoint; the preceding
self-play checkpoint was preserved. Large models/data are ignored by Git. No
rank or reliable win rate is established. Updates prove learning machinery runs,
not that skill improves. No public/ranked matchmaking automation exists.

## Fly Purity disclosure

A single percentage is not a validated metric. Profile: real connectivity and
graph in every decision: yes; anatomical plasticity/validated physiology: no;
engineered perception, legality, GRU and human reward/item knowledge: yes;
scripted tactics: no. Compare native-memory-only, no-imitation, no-guide-reward,
shuffled-graph and disconnected-graph ablations before claiming anatomy advantage.

Next: richer visibility-correct replay labels, frozen-policy farming/death/objective
comparisons, terminal/restart verification, then throughput and parallel scaling.
