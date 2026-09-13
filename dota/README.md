# Controlled Dota integration: staged, not engine-tested

Selected route: an isolated **Workshop Tools custom addon**, with the frozen
connectome reservoir and action readout exported to Lua and executed inside
VScript. No desktop controls, memory reading, injection, external HTTP controller,
Steam credentials, matchmaking or public/ranked queues are implemented.

`addon/scripts/vscripts/addon_game_mode.lua` is an adapter scaffold, **not a
complete runnable custom map**. It refuses activation outside `IsInToolsMode()`.
The Python toy results do not establish Dota compatibility or performance.

## What was inspected locally

Dota installed at `C:/Program Files (x86)/Steam/steamapps/common/dota 2 beta`, build
25265195. The shipped `game/dota_addons/last_hit_trainer/scripts/vscripts/`
contains an actual last-hit trainer using `SetThink`, `CreateUnitByName` and
`ExecuteOrderFromTable`. Read-only inspection; no installed files changed.
`dota2cfg.exe` and `hammer.exe` were not found in the checked game tree. Install
the optional Dota 2 Workshop Tools through Steam to author and test the fixture.

## Reproducible next integration test

1. Enable Workshop Tools, create a separate addon `fruit_fly_dota_lane` and an
   empty flat test map. Use the installed last-hit-trainer as a reference; do not
   overwrite it. Record client build, map checksum and addon commit.
2. Copy this adapter and generated `fly_policy.lua` into that addon's vscripts.
   Generate inference with `python -m fruit_fly_dota.export_lua` from repo root.
3. Build a fixture that selects one fixed melee hero, spawns one stationary creep,
   fixes items/armor/damage/attack speed, randomizes initial positions by a logged
   seed, applies controlled background damage and resets on death or timeout.
4. On reset call `FlyLaneReset()`. At a fixed decision cadence, assemble the six
   fields in `observation.py` from player-visible telemetry; call `FlyLaneStep`.
   Visibility must be checked before serializing target data. Supply no future
   damage, enemy-in-fog state, teacher output or hidden server timers as input.
5. Instrument attack launch/impact/cancel, cooldown, range and movement. The toy
   parameters are not real Dota timings: calibrate units and rebuild/retrain the
   observation schema before claiming transfer. In particular, Dota attack orders
   can auto-repeat whereas toy attacks are single attempts; enforce a single
   attempt in the fixture without canceling the projectile or adding aiming logic.
6. Log observations, requested orders, applied orders, timestamps, rewards and
   `entity_killed` attacker attribution. Timeout/stop must disable new orders and
   stop the controlled hero. Test missing/stale/dead targets and interrupted attacks.
7. First execute fixed scripted actions; then compare Python and Lua inference on
   identical recorded observation sequences. Only after that run learned policy.
8. RL comes after reset, reward attribution, deterministic seeding and observation
   parity are verified. Implement episodic trajectory export and offline updates,
   then reload the exported policy between rounds. No Dota RL has run yet.

Sources: [Valve scripting API](https://developer.valvesoftware.com/wiki/Dota_2_Workshop_Tools/Scripting/API),
[ModDota maintained API](https://moddota.com/api/),
[ModDota scripting introduction](https://moddota.com/scripting-introduction).
Valve's web wiki could not be read in this session; installed Valve Lua sources
provided the primary evidence for the order/spawn/timer route. APIs still require
an engine smoke test against the installed build.
