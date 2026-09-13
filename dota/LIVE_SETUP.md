# Full model: real-map integration

This path uses Valve's standard `dota` map, with an isolated addon called
`fruit_fly_dota`. It does not replace built-in addons or use matchmaking.
Install Dota 2 Workshop Tools from Steam first.

**Engine status, September 13:** live observations, full-model inference, movement
orders and position changes verified in build 25265195. Stop command verified.
No attack/spell impact or real-game learning result yet. Two initial late-spawn
attempts crashed while cosmetic resources were unloaded; player-aware asynchronous
precaching resolved the tested spawn failure. The controller is stopped after tests.

From the repository root, after building the full model:

```powershell
.\.venv\Scripts\python.exe -m fruit_fly_dota.live
```

In another terminal:

```powershell
.\scripts\install_dota.ps1
```

Alternatively `scripts/launch_dota.ps1` installs and launches the local map when
Dota is closed. It does not change your saved Steam launch options.

Launch Workshop Tools for `fruit_fly_dota`, open its Valve console, and run:

```text
dota_launch_custom_game fruit_fly_dota dota
fly_start
```

`fly_stop` disables new requests, invalidates pending replies and stops the unit.
The controller binds only 127.0.0.1:8765 and accepts a bounded 16-number observation
plus a 13-entry legal mask. Run only on a trusted local workstation; this development
endpoint has no authentication or multi-client/session isolation. One game per server.
Restart the controller for an independent run to reset the random generator too.

## Scaffolding inventory

- Plain Lina hero unit spawned for local player 0 at a fixed Radiant location.
  This bypasses normal hero selection for a smoke test; no other hero bots yet.
- Engineered 16 inputs: position, HP/mana fractions, level, gold, attack range,
  game clock, nearest visible enemy displacement/HP/presence/hero flag, three spell
  availability flags. No fogged target telemetry. No inventory or global strategy.
- Nearest-visible target selection is **engineered target prioritization**; it
  limits the current policy and must be replaced by selectable target slots.
- Engineered 13 actions: wait, eight 250-unit compass moves, attack selected target,
  Dragon Slave, Light Strike Array, Laguna Blade. Spell levels are not allocated
  by this policy yet, so spells remain masked until separately leveled for tests.
- Network state persists between decisions; no additional temporal memory.
- The random linear decoder and stochastic action sampling are **untrained**.
  Game observations cannot bypass the recurrent sensory-to-motor pathway, but
  the legal mask influences action choice outside the graph and exploration adds
  randomness. Lesion tests must compare distributions and performance accordingly.
- Requests run no faster than 5 Hz, one in flight; replies older than 1.5 seconds
  are discarded. Enemy validity/visibility is rechecked before a target order.
- `work/live.jsonl` records requested neural actions and observations. `FLY_ORDER`
  in the Dota console records issued engine orders, not confirmed attack impact.
  Raw client console logs can contain account metadata; do not publish them.

## Next milestones toward full matches

1. Verify engine-observation-request-order round trip and stop behavior.
2. Add action acknowledgments, damage/kill/objective rewards, resettable episodes
   and recording of demonstrations in real Dota. Train the full decoder on those
   sequences, then compare intact, shuffled, disconnected and memory-reset models.
3. Add selectable targets, skill allocation, items/shop, courier and teleport;
   introduce allied/enemy bots and evaluate complete local matches.
4. Replay imitation uses parsed `.dem` data only when observable state and labels
   are aligned; YouTube footage is secondary and needs uncertain action labels.
5. Report win rates against named bot versions, side/hero/seed coverage, farming,
   deaths, objective damage and invalid actions. Human MMR remains unknown until
   an independently justified calibration exists. Fly Purity is a disclosed
   engineering audit, not proof of biological intelligence.

The [ModDota tutorial](https://moddota.com/scripting-introduction) documents reuse
of the standard map. Actual APIs are checked against the installed Workshop build.
