# Full model: real-map integration

For the new explicitly assisted mode and online reward updates, see
[live learning](../docs/LIVE_LEARNING.md). The unassisted setup below remains
available on a fresh map without `fly_play`.

This isolated Workshop Tools addon uses Valve's standard `dota` map. It does not
replace stock scripts or use matchmaking. Install Workshop Tools through Steam.

## Run

Build the dataset following [full model setup](../docs/FULL_MODEL.md), then run:

```powershell
python -m fruit_fly_dota.live --policy results/sf_replay/policy.npz
```

In another terminal run `scripts/install_dota.ps1`. With Dota closed,
`scripts/launch_dota.ps1` also installs and launches the map without changing
saved Steam launch options. In the Workshop console:

```text
dota_launch_custom_game fruit_fly_dota dota
fly_start
fly_match
```

Open <http://127.0.0.1:8765/> for actual sampled neural states and symbolic action
keys. `fly_camera_follow` tracks SF; `fly_camera_free` releases the camera.
`fly_stop` disables requests, invalidates pending replies and stops the hero.

## Verified and unverified

On September 13, build 25265195 verified full-model observations and movement,
camera tracking, stop behavior, and creation of nine bots. Corrected late hero
creation now places SF at the map's Radiant spawn (-6700,-6700), rather than
origin. Player-aware resource preloading avoids the previously observed crash.
The first trained rollout got stuck repeating a direction. No completed full
match, learned shopping, successful spell impact or competitive rank is verified.

## Disclosed scaffolding

- Normal SF hero creation after asynchronous precaching; engineered Radiant
  spawn/respawn placement and 600 starting gold configuration.
- Seventeen transport fields: position, HP/mana, level, gold, range, clock,
  nearest visible enemy displacement/HP/presence/hero flag, and four cast flags.
  The shipped checkpoint uses only own position, HP, mana and level; other
  fields are zeroed before neural input to match replay training.
- Fourteen actions: wait/continue previous order, eight compass moves, nearest
  visible target attack, three razes, and Requiem. Target prioritization and
  legality masking are engineered. Raze aiming is not automatic.
- Fixed biological connectivity with simplified rate dynamics, native recurrent
  state and an engineered trained linear readout. Omitting `--policy` uses an
  explicitly untrained random decoder. Neither is validated brain physiology.
- Fixed spell-upgrade priority in match mode is engineered, not learned.
  Shopping, item use, courier, talents, teleport and buyback remain incomplete.
- At most one request in flight, normal one-second decision cadence, cast-phase
  and channel guards. Replies older than 1.5 seconds are discarded. Target
  visibility and validity are rechecked before attack orders.
- Local unauthenticated development endpoint on 127.0.0.1:8765. One game per
  server. Seventeen bounded observations and fourteen legal bits are validated.
  Restart the server for an independent run; `seq=0` resets neural state.
- JSONL logs record requested actions; `FLY_ORDER` records issued engine orders,
  not confirmed effects. Raw client console logs may contain account metadata
  and must remain local.

See [SF training](../docs/SHADOW_FIEND.md) for the five-match dataset, weak first
results, parser provenance, limitations and outstanding full-player controls.
Next evaluation needs action acknowledgments, attack/damage/objective rewards,
complete match outcomes, and intact/shuffled/disconnected/memory-reset controls.
Win rate against named bots is a future metric; human MMR remains unknown.
