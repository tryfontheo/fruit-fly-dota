# Unassisted decision learning, observation/action schema v2

The user rejected scripted tactical assistance. The live addon no longer loads
the historical assistance module. No mid-lane route, attack-move, automatic
retreat, fixed shopping order or fixed skill priority controls SF. Idle target
acquisition is disabled. `fly_play` now only populates bot players, like
`fly_match`; neither supplies SF strategy. Assisted payloads are rejected by the
Python controller. Historical assisted results are not results for this policy.

## Run

```powershell
python -m fruit_fly_dota.live --learn --log work/unassisted-v2.jsonl
```

Install the addon and load the local standard map, then use `fly_start` and
`fly_match`. Open <http://127.0.0.1:8765/>. `fly_stop` stops the controller.
This separate run starts an untrained decoder, retaining the real fixed MaleCNS
graph. The old pro-replay and assisted checkpoints are preserved, but their
17-input/14-action shapes are incompatible with v2. Do not pass them with
`--policy` or `--resume-learning`. Reuse checkpoints only with identical schema,
base policy and model. Old replay recovery requires the matching code revision.

## What the network sees and chooses

All 33 observation fields stimulate the neural model: the original 17 own-state
and nearest-visible-enemy fields; visible nearest tower displacement, range and
presence; available skill points; four skill levels; and counts of seven listed
items. Tower information is supplied only while visible. There is no suggested
move, route, retreat threshold or teacher action in the inputs.

The 25 choices are wait/continue, eight compass moves, attack, three razes,
Requiem, four skill upgrades (raze, aura, Frenzy, Requiem), and seven basic item
purchases (boots, gloves, Band of Elvenskin, lifesteal, broadsword, Blade of
Alacrity, Yasha recipe). A neural choice is required for every upgrade/purchase.
This remains an incomplete player vocabulary: e.g. talents, courier, arbitrary
targets, Frenzy activation, item use, teleport and buyback are not implemented.

Mechanical scaffolding remains explicit: structured observations, nearest-visible
target slot, legal-action masks, fixed compass distances, and the paid fountain
shop adapter. The latter checks price/proximity/inventory capacity; it has no
item priority. Dota still supplies pathfinding and normal attack-order behavior.
Removing scripts does not turn this into a physiological full-brain simulation.

## Damage feedback

Enemy damage to SF now gives -2 times the fraction of maximum health represented
by reported damage. Tower damage uses -4 times that fraction instead. Each event
is capped at one full health bar, and negative/missing damage gives zero. Losing
10% HP is therefore -0.2 normally or -0.4 from a tower. Death still gives -3.
Friendly/self-inflicted damage is excluded. Damage and death penalties can both
apply to a lethal hit; healing is not rewarded. The existing kill/objective and
idle signals remain. These coefficients are initial experimental reward shaping,
not a validated optimal strategy or measured biological dopamine.

The reward changes the engineered decoder adapter via eligibility traces; no
damage handler issues a retreat or attack order. The recurrent connectome stays
in the observation-to-action loop. There is no evidence yet that this policy has
learned tower avoidance or full-match competence. Exploration from the fountain
has sparse useful feedback; controlled training encounters and aligned replay
pretraining are the next practical training work, not hidden tactical rules.
