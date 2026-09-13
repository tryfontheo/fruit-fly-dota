# Live reward learning and assisted play

Historical assisted mode at commit a066314. The user subsequently rejected
tactical scripts; see [current unassisted mode](UNASSISTED.md). Commands and
checkpoint shapes below describe that earlier implementation.

This is an experimental dopamine-like scalar reward, **not biological dopamine**.
All 176,422 model neurons still run. Anatomical connections remain fixed. Only a
separate engineered linear action adapter changes online.

```powershell
python -m fruit_fly_dota.live --policy results/sf_replay/policy.npz --learn --log work/session.jsonl
```

Install the addon, load the standard local map, run `fly_start`, then `fly_play`.
`fly_play` explicitly enables heavy scripted assistance. `fly_start` alone uses
the original action mapping on a fresh map. Reload the map to remove assistance.
`fly_stop` stops the controller. Public/ranked matchmaking is never used.

## Reward contract

| Observed event | Reward |
|---|---:|
| Enemy creep killed by SF | +0.25 |
| Enemy real hero killed by SF | +3 |
| Enemy building killed by SF | +2 |
| SF damage to enemy building | +0.001 per damage, capped at +0.2 per event |
| SF death | -3 |
| Ten idle checks, no visible target, HP above 90% | -0.1 |

Game events identify the controlled hero as attacker. No reward is given merely
for issuing an order, buying an item, spending gold or watching an animation.
Pending rewards are bounded to [-20,20] and delivered with the next observation.
Death rewards currently wait until respawn. A network failure can drop feedback;
this is a development bridge, not a fault-tolerant training service.

Reward updates the previous policy-gradient eligibility trace, then the next
decision is sampled. The trace decays by 0.8 per decision; learning rate is 0.02.
The neural motor features are normalized and the bias feature is excluded from
plasticity. Adapter weights are clipped to [-5,5]. This simplified rule has no
reward prediction model, calibrated dopamine concentration or demonstrated
biological time constants. Rewards and update counts do not prove improvement.

## Assistance and scientific limits

The scripted layer provides a mid-lane waypoint route, attack-move, low-health
retreat, a fixed spell-upgrade priority and a short fixed basic-item build.
Neural movement choices vary offsets on that route; attack-move lets Dota choose
and attack enemies automatically. Thus many decisions and successful hits can
be explained by engineering outside the connectome. The dashboard says
SCRIPT-ASSISTED, and logs retain that flag. This is a playable development
baseline, not evidence that a fly learned full Dota strategy.

The native scripted purchase order was rejected by the engine. The explicit
custom-shop fallback checks fountain proximity, available inventory space and
the current item price, adds an unlimited-stock basic item, then spends that
amount of the hero's gold. This bypasses the normal shop UI, stash and courier;
it is not a learned shopping policy. No extra gold is granted for purchases.

Under the historical subjective purity rubric, assistance earns zero "no policy
bypass" points. The bookkeeping total would be 37/100 (30 connectivity, 2
physiology, 0 anatomical I/O mapping, 0 biological learning, 5 recurrence, 0
bypass). This poorly captures the large effect of scripts and is NOT a percentage
of intelligence attributable to the fly. Scaffold-only and disconnected controls
must precede causal claims; no rank or win-rate result is available.

## Checkpoints and verification

The server saves `work/session.learning.npz` every 25 decisions. Resume it with
`--learn --resume-learning work/session.learning.npz` and the same base policy,
model and action mapping. Recurrence and eligibility reset for a new episode;
learned adapter weights persist. Do not compare runs with different assistance
settings as if only the learning algorithm changed.

Windows interrupted the first process before its exit save. The complete initial
135-decision log was replayed with `scripts/recover_learning.py`; every sampled
action matched before saving the recovered 11 updates. Recovery requires the
identical initial seed-zero policy and a complete initial log, not an already
resumed run. Periodic checkpoints now avoid relying on graceful shutdown.

Engine observations verified SF leaving base, reaching mid, gaining levels,
receiving last-hit and objective-damage rewards, and receiving a death penalty.
The paid shopping fix deducted the current 500-gold boots price. Nine bot players
spawned; their strategic behavior and a completed match outcome remain unverified.
Tests cover reward direction, credit reset, disconnected signal and duplicate
sequence rejection. No claim of improved performance from online learning yet.
