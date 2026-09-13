# Replay imitation and video data

Selected parser: [Clarity](https://github.com/skadistats/clarity), with
[official examples](https://github.com/skadistats/clarity-examples). Its repository
documents Java 17+, entities, combat logs, modifiers and user messages. Check
parser version against the replay's Dota build. [OpenDota](https://github.com/odota/core)
uses replay parsing for analytics; aggregate statistics alone are not imitation
state/action trajectories. Neither tool was installed or run against a replay
here because no `.dem` was supplied. The Python loader is an interchange validator,
not a claim to decode Source 2 demos.

Prefer our own controlled-environment order logs with known observations/actions.
For external `.dem`: record match ID, build, parser commit, hero/player, source
checksum and extraction settings. Reconstruct player-visible state at decision
time; do not leak spectator positions, hidden wards or future combat outcomes.
Verify which player orders the particular replay actually contains. Spectator
clicks and inferred movement are not necessarily player commands. Label inferred
actions separately, with confidence; the current loader deliberately accepts only
recorded orders, human labels or disclosed synthetic teacher labels.

Normalize to newline-delimited JSON, one decision per row:

```json
{"schema":"fly-dota-demo-v1","episode":"toy-example-1","tick":0,"perspective":"player_visible","action_source":"synthetic_teacher","observation":{"hero_x":0.1,"target_x":0.7,"target_hp":90,"cooldown":0,"windup":0,"visible":true},"action":2}
```

This example uses toy units. Actual Dota telemetry requires a documented unit
conversion/calibration and aligned action timestamps, not relabeling live values.
Split complete matches/episodes into train, validation and test **before** feature
extraction/windowing; never randomly split adjacent frames. Reset recurrent state
at episode boundaries. Archive source provenance next to each normalized file.

`python -m fruit_fly_dota.cli imitate --demos path/to/train.jsonl --rl-episodes 0`
fits the readout from this interchange and reports **toy lane** evaluation only.
It does not evaluate match performance or automatically split your dataset; supply
only the train split. Offline held-out action accuracy and in-engine evaluation
must be added for a real replay dataset.

YouTube player-perspective video is secondary: use recordings the user can supply
or download legitimately, preserve timestamps/frame rate/HUD/camera coverage, and
annotate visible-state/action uncertainty. Object detection, OCR, camera tracking
and any action recognizer are additional engineered intelligence and must appear
in the purity ledger. No video pipeline or pretrained vision network is hidden
inside this prototype. Cross-view spectator video is not clean action ground truth.
