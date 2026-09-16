# Shared recurrent self-play

Free camera is the default; `fly_camera_follow 0` is an explicit opt-in.
Training uses an adaptive 0.5–4x game-speed controller. It increases speed in
0.5 steps and aims to keep p95 response delay below 1.2 game seconds; request
failures trigger a reduction. `fly_speed_max 2` caps it at 2x, or use 1 for normal
speed. It enables local tool cheats for the time-scale cvar, without granting
items/gold/levels. This is a latency guard, not proof that high speed preserves
combat quality. Physical command timeouts use `GetSystemTimeMS` wall time instead
of server game time. See [server API](https://docs.moddota.com/lua_server/).

Reward trial `lane-v4-exploration` reduces damage penalties to -0.5 per full HP
equivalent, tower damage to -1 and death to -1 (previously -2, -4 and -3).
Farming/XP rewards are unchanged. The rationale is to reduce early avoidance;
this is an unproven reward hypothesis, not evidence of improved play. The model
before the change is preserved as `work/before-exploration-v4.pt`. Historical
outcome review: `results/recurrent/pre_exploration_review.json`; generate a new
review with `scripts/report_learning.py`. Do not compare raw shaped returns
across reward versions as if their meaning were unchanged.

## Faster contact curriculum

**Start-Fast-Training.cmd**, or option **5** in the desktop menu, starts 5v5 with
a lane-placement curriculum. After 45 game seconds each living hero is placed
400 units behind its team's most advanced living lane creep (distance from base).
Candidates within an enemy living tower's attack range plus 300 units are rejected;
if none qualify, placement waits. This is privileged reset generation, not a policy
observation or learned tower avoidance.
Unavailable/dead heroes wait until placement is possible. A hero with no new XP
for 120 game seconds receives another placement. This avoids long unproductive
stretches but does not demonstrate learned navigation. No health, levels,
items or gold are granted. Subsequent actions and ordinary base respawns remain
under the existing learner/game rules. Placement marks a recurrent episode boundary.
For 30 game-seconds after each placement, TP-to-base is masked and rejected again
at execution. In-flight decisions from before the placement are discarded.
This explicit curriculum constraint prevents immediate reset-to-fountain loops;
it is not learned retreat behavior and does not apply to ordinary self-play.
This is engineered initial-state training, not learned navigation. It clusters
heroes near waves and may overrepresent fights; compare base-start evaluations.
It is intended to increase meaningful contacts, not a proven sample-efficiency gain.
`FLY_LANE_START` records placements in the Dota console log. Keep curriculum
results separate from ordinary match evaluations. **Start-SelfPlay.cmd** retains
normal base starts. The pre-curriculum local model is backed up as
`work/before-lane-start-v6.pt`.

Home TP is masked within 1,600 world units of its destination and rechecked
immediately before execution, including mute/readiness. This is the user's
requested anti-waste training constraint, not a learned judgment or an engine
legality rule. Outside that radius the policy still chooses whether to TP.

**Run-Fruit-Fly.cmd** is the simple menu: start 5v5, start lane practice, open the
dashboard, check training/saves, or open VConsole2 with option 6. Selecting a mode
automatically restarts an existing local fly match, keeping the trainer running.
Close any unrelated Dota game first. Keep
Steam signed in, and leave the computer awake. Closing the menu does not stop
training. Close Dota to stop game experience; the trainer waits for the next launch.
The desktop launcher on the configured PC opens this menu. It depends on this
repository and its installed environment; it is not a portable standalone executable.

Run **Start-SelfPlay.cmd** for local 5v5, or **Start-Training.cmd** for lane practice.
The selected addon mode loads automatically. No console commands or file hunting are needed. Watch
http://127.0.0.1:8765/ and select player 0–9. `fly_camera_follow 0` follows SF;
`fly_camera_free` releases the camera; `fly_stop` stops all agents.

Training runs locally without Codex credits or messages. It saves atomically every
100 decisions and at terminal results to `work/shared-v6.pt`, restoring weights
and optimizer on restart. Keep that file. Logs are `work/shared-v6.jsonl` and
`work/trainer.log`. The supervisor restarts failed Python workers after five
seconds. Dota crashes require relaunching. Keep the computer awake. Temporary
per-hero memory resets for new matches/processes; learned weights persist.

## Architecture

78 structured observations → 176,422-neuron MaleCNS connectivity-derived rate
dynamics → 64 motor features → engineered 64-unit GRU → 54 legal-masked actions.
There is no raw-observation bypass. Anatomical weights remain fixed; GRU, actor
and critic learn. This is not validated full-brain physiology or biological
dopamine. Each hero has independent neural/GRU state; all share policy weights,
not private fog observations. Recurrent PPO now pools 1,024 transitions, uses 32-step
chunks and three epochs. Version checks reject stale transitions; failed orders
discard only the unacknowledged pending action. Earlier completed transitions
are retained, with credit traces and recurrent chunks cut at the gap.
The farming-v5 trial uses per-game-second discount 0.999 (previously 0.99)
and GAE trace 0.99 (previously 0.95). Reward half-life is about 693 seconds
instead of 69; this does not make a terminal win directly supervise every
early decision. Value bootstrapping is still necessary across short rollouts.
Checkpoint metadata records the settings used when saving; restarting uses
the current code defaults, retaining weights, optimizer and random state.
The pre-trial brain is backed up locally at `work/before-farming-v5.pt`.
`scripts/report_learning.py` reports actual farming kills and XP, normalized
for the reward-version change, plus healthy TP choices and base occupancy.
TP choices are issued decisions, not proof that a teleport completed. Base
occupancy is a fraction of observations, not a wall-clock occupancy measure.
Compare frozen policies under identical curricula before claiming improvement.

Training batches independent recurrent chunks instead of evaluating every example
serially. A CPU comparison including one 256-sample update took 0.449 seconds
serially and 0.103 seconds batched (4.35x for this isolated workload). Maximum
parameter difference was 7.1e-8, including a terminal transition. See
`results/recurrent/batched_ppo.json`. This excludes full-graph simulation and Dota;
it does not establish a 4.35x game-speed or sample-efficiency improvement.

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

54 action slots cover wait, eight movement directions, four visible enemy target slots,
three razes, Frenzy (R), Requiem (Y), four skill upgrades, eight talents, seven
disabled legacy component slots, eight guide items, five item activations, visible rune pickup,
stop, TP purchase and TP to base. These are game orders, not physical key presses.

Guide items: Power Treads, Mask of Madness, Dragon Lance, BKB, Silver Edge, Satanic,
Daedalus and Butterfly. Activations: MoM, BKB, Silver Edge, Satanic and Treads toggle.
V6 enforces the user's one-copy item constraint across inventory/backpack/stash.
Loose component buying is disabled because the adapter purchases complete items
without using them. These are explicit engineered shopping constraints, not
learned item efficiency. The old v5 checkpoint remains preserved.

V6 appends nearest allied lane-creep displacement, presence and team side, taken
from allied minimap information. No enemy fog information or scripted navigation
is supplied. Existing 74 encoder columns and the trained policy are preserved
by `scripts/migrate_wave_checkpoint.py`; new input semantics still need learning.
The signal identifies an allied creep, not guaranteed enemy contact or optimal farm.
Providing it is not evidence of learned wave navigation.
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
