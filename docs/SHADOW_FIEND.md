# Shadow Fiend experiment

The target hero is now Shadow Fiend (`npc_dota_hero_nevermore`, hero ID 11).
The older Lina movement result remains historical evidence, not an SF result.

## Real data

`scripts/collect_sf_replays.py --count 6` searches OpenDota's public professional
and premium league catalog for SF and downloads the available Valve replay.
Some current Valve `.dem.bz2` URLs actually contain Zstandard. The collector
detects magic bytes, decompresses, checks Source 2 format, and records SHA-256.
Use the optional `replays` dependency for Zstandard support.

Six replays were obtained; one with unnamed player/incomplete selected-hero
tracking is excluded from training. The other five include 423, jikroy, Straight
Edge, Lumière, and Timado. Whole-match train/validation/test assignments are in
`data/replays/sf_manifest.json`. The split is not random adjacent frames.
Raw replays and parser debug output stay local. Public manifests contain public
match metadata; source replay files are not rehosted on GitHub.

Parser: Clarity 4.0.1, using clarity-examples revision
`10be1dedba0e15b51b509cda3a043d50655c89f8`. Our extractor is `tools/replays/Main.java`.
The local portable Temurin JDK 21 is under `work/replay-tools/jdk`; no global Java
settings changed. The examples' Gradle toolchain is locally adjusted from 17 to 21.
Build as `flyextractPackage` after copying the extractor to the examples'
`src/main/java/skadistats/clarity/examples/flyextract/Main.java` directory.
Invoke the jar with replay path, selected player index and output JSONL path.
For normal match slots, Radiant uses 0–4; Dire 128–132 maps to indices 5–9.

## Initial training scope

`python -m fruit_fly_dota.train_sf --per-match 600` encodes up to 600 uniformly
sampled decisions per match through all 176,422 selected neurons, then fits an
engineered linear decoder. Biological recurrent connections remain fixed.
Only current own position, HP fraction, mana fraction and level enter this
checkpoint. It does not reconstruct opponent vision, souls, inventory or facing.

Labels are deliberately distinguished:

- Movement direction and stationary behavior inferred from the next one-second
  position change. Displacements over 550 units, death boundaries and gaps excluded.
- Attack activity inferred from damage without an identified ability. This is an
  imperfect proxy for attacks, not exact order/attack-launch timing.
- Named SF spell casts from recorded combat-log events. At most one prioritized
  action is assigned to each window, losing combinations within that second.

Future events are labels only; none enter input features. Subsampling compresses
time in recurrent state; this is a coarse pretraining experiment, not faithful
biological timing. The self-state-only checkpoint cannot learn proper raze aiming
or enemy-dependent tactics. Holdout accuracy and a disconnected-graph comparison
are recorded before in-game evaluation. A high score alone would not establish
competent Dota play.

## Watching

Run the local server, open `http://127.0.0.1:8765/`, and start the addon with
`fly_start`. `fly_camera_follow` tracks SF, `fly_camera_free` releases the camera.
The compiled Panorama HUD selects the controlled unit and displays actions.
The dashboard displays 240 actual sampled model states in schematic positions,
64 engineered motor pools, and symbolic Q/W/E/Y keys. The user's saved SF-specific
quickcast bindings were checked: Q/W/E/R/T/Y, with Y for ultimate. R/T do not yet
have policy actions. The engine receives orders
directly; these are not operating-system key presses. Stale data is labeled stopped.

## Local match evaluation

The `fly_match` command requests default bots in remaining slots on the standard
map. This route must be engine-verified; a request alone is not proof of a match.
The console verified creation of nine bot players, but a completed match has not
been observed. The first trained live rollout got stuck repeating northeast
movement. Its own-state-only input omits obstacles and navigation goals.
SF uses normal hero creation and resource preloading. A fixed, disclosed skill
priority is engineered scaffolding; item shopping is not yet automated. The
readout chooses movement, nearest-visible-target attack, three no-target razes,
and Requiem. There is no auto-aim for razes. Full-match competence and MMR are unknown.

## Measured first checkpoint

The test match has 600 sampled decisions: accuracy 50.17%, training-majority
baseline 41.0%, balanced accuracy 15.40%. Disconnecting the graph with the same
decoder yields 6.67%; this is not a retrained control or proof that fly topology
outperforms other recurrent wiring. The optimizer reached its 500-iteration cap
without convergence. Only three ultimate examples occur in the training set.
See `results/sf_replay/metrics.json` for full counts and provenance.

## Purchase extraction and remaining controls

The extractor now records SF-targeted combat-log purchase events before filtering
attacker events. A held-out Timado replay yielded 38 records. These include both
components and completed items, so they must not all be treated as independent
shop clicks: inventory/recipe reconciliation is still required. This replay stays
held out; inspecting parser output does not add it to training.

Shopping is not implemented in the live policy. Skill allocation currently uses
a disclosed fixed priority, not learned decisions. Learned upgrades, talents,
inventory use, courier, teleport, buyback and objective strategy remain pending.
No full-player capability or rank should be inferred from the current demo.
