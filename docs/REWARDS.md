# Current reward trial: lane-v6-fountain-cost

Healthy fountain camping costs -0.02 per game-second after 15 continuous seconds
within 1,600 units of the own-team spawn, with HP and mana both at least 90%.
It starts only after game time 45 seconds and never charges dead heroes. Leaving
the zone or dropping below either threshold resets the grace period. This is an
engineered opportunity-cost experiment; it can teach boundary camping or repeated
visits instead of farming, so lower base occupancy alone is not success. There is
no movement reward or scripted exit action. Brief recovery/shopping is allowed;
this cannot recognize every legitimate reason to stay at base.

Damage taken now costs -0.5 per full HP equivalent, tower damage -1, and death
-1. Last hits (lane or jungle) now earn +2 and each new XP earns +0.002.
Damage budgets, rune, item and spell rules are unchanged. This doubles productive
farming credit without rewarding fountain healing, motion or mere survival.
This reduces the earlier survival penalties as an experimental response to
fountain avoidance; improvement has not been established. See
[current training setup and evidence](SHARED_POLICY.md). Old values below record
the previous versions and must not be mistaken for the active penalty scale.

# Historical reward design: lane-v2

These are experimental, engineered teaching signals. Positive reward strengthens recently selected actions through a connectome-dependent readout; negative reward weakens them. They are not measured dopamine, nor a validated biological punishment circuit. Reward design introduces human knowledge even when there are no tactical scripts.

## Enabled now

| Outcome | Reward | Why / limitation |
|---|---:|---|
| Enemy creep damage | Up to +0.10 across that creep's lifetime | A small discovery signal; 10% of its max HP earns +0.01. Regeneration cannot refill the reward budget. Damage is not always strategically desirable: this may encourage pushing waves. Compare against a damage-reward-off ablation. |
| Enemy creep last hit | +1.00 | Ten times the entire creep-damage budget; farming should value the finishing hit. No additional reward for the same bounty gold. |
| Allied creep deny | +0.30 | Event hook exists, but the current action vocabulary cannot deliberately target allies; not claimed as a working learned behavior. |
| Enemy real-hero damage | Up to +0.50 per unit lifetime | Small harass signal; no reward for illusions classified outside these targets. Respawning heroes reuse their handle, so this budget remains exhausted until a new hero entity is created. |
| Enemy hero kill | +3.00 | Larger than incidental damage. Future team contribution credit is needed to avoid kill-stealing incentives. |
| Enemy building damage | Up to +1.00 per building lifetime | Encourages lasting objective progress; prevents unlimited healing/damage farming. |
| Enemy building destruction | +5.00 | Objective completion matters more than poking. Building categories are not yet distinguished. |
| Damage taken | -2.00 per full max-HP equivalent | 10% HP costs -0.20. This is an imperfect surrogate: taking damage can be correct in a favorable trade. |
| Tower damage taken | -4.00 per full max-HP equivalent | 10% HP costs -0.40. Stronger early warning against dives; successful dives/tanking may be unfairly discouraged. |
| Death | -3.00 | Applied in addition to preceding damage penalties. No further penalty for death gold loss. |
| Waiting, walking, casting, spending gold, leveling a skill, healing at fountain, passive income, training resets | 0 | Inputs and conveniences are not achievements. Removed the idle penalty, which could reward purposeless motion. |

Damage rewards depend on reported damage after mitigation and are capped by a per-unit fractional budget. They do not exactly reconstruct pre-hit HP, so overkill attribution can be imperfect. Budgets use weak entity-handle keys and persist across round resets; cleanup creates no kill reward. Damage to one's own team is not rewarded. Reward components are logged separately from their clamped scalar sum; transport reward remains clipped to [-20,20].

Passive gold is granted by an explicit game-clock timer through `PlayerResource:ModifyGold` at **1 gold / 0.6 seconds = 100 GPM**, a reproducible practice setting rather than a claim of exact current ranked economy parity. It awards no learning reward. API reference: [ModDota's generated server API](https://docs.moddota.com/lua_server/) (`SetGoldPerTick`, `SetGoldTickTime`). Previously observed gold stayed at 600 over 111 seconds. Explicit native tick settings also failed to credit income in a subsequent live test. Native ticks are therefore disabled, preventing double payment; the fallback timer pays all valid player IDs 0�23, runs independently of the neural action rate, and does not advance during paused game time.

## Candidate signals for a fuller player — not enabled yet

| Area | Good outcomes to consider | Bad outcomes / safeguards |
|---|---|---|
| Match result | Winning should eventually dominate local shaping | Losing; do not mistake round survival for a match win. Need actual completed bot games and terminal credit. |
| Objectives | Towers, barracks, Ancient, Roshan and securing useful objectives with the team | Losing objectives; avoid paying twice for building damage, destruction, team net worth and victory at overwhelming scale. |
| Economy | Last hits, denies, earned bounty, efficient farm progression | Do not reward passive gold, item selling, repeated purchases, or raw wallet increases. Purchase decreases cash but preserves value. |
| Experience | Actual XP and level progress as a small potential-based signal | Standing within XP range can be legitimate. Do not reward merely standing near creeps each frame. Avoid double-paying kills + XP too strongly. |
| Trading | Meaningful enemy health/resource advantage while retaining ability to farm | Damage alone can reward suicide. Compare resource exchange and subsequent outcomes, with only observable enemy state. |
| Spell use | Raze hits, productive multi-unit casts, kills/objectives enabled by Frenzy or Requiem | No reward simply for pressing a spell. A missed spell can zone/save a teammate, so an automatic miss penalty is not universally correct. Mana loss already changes future options. |
| Survival | Surviving an engagement with a favorable trade; escaping a dangerous situation | Permanent survival bonuses encourage fountain camping. Death penalties alone can create an overly timid agent. No healing loop rewards. |
| Team play | Assists, successful saves, useful disables, taking an objective together | No indiscriminate proximity rewards. Need event attribution and opportunities to act on allies. |
| Items and skills | Useful effects, stronger subsequent farming/fights, actual progression | No prescribed build, no reward per purchase/upgrade. Buying duplicate useless items must not print reward. Broader inventory/courier/talent actions are still needed. |
| Map play | Securing resources/vision and reaching objectives when they matter | No reward just for moving, revealing empty map, placing arbitrary wards, or following a fixed route. Vision information must obey fog. |
| Execution | Commands that successfully achieve intended effects | No APM bonus. High APM can repeatedly cancel attacks. Invalid-action penalties alone mostly teach the legality wrapper. |
| Opportunity cost | Missing a genuinely available last hit or arriving too late to a useful objective | Hard to measure without a scripted expert or hidden information. Keep diagnostic initially, not automatic punishment. |

## How to tell whether the rewards help

Log last hits/minute, deaths/minute, creep damage, hero damage, gold earned excluding passive income, XP, objective completion, command rate, canceled attacks, and each reward component. Currently only a subset is available; do not present the whole list as implemented metrics.

Run several seeds, then evaluate frozen checkpoints under the same starts/hero levels against a random decoder and the previous checkpoint. Compare sparse last-hit/death rewards against damage shaping. Retain a no-learning control and a shuffled/disconnected-connectome ablation. Ultimately use full-game win rate against specified bots, not shaped return or an invented ranked MMR.

The prior adapter is retained, with a local backup `work/before-lane-v2.learning.npz`. Logs tag the new reward version `lane-v2`; do not compare cumulative reward across the version change as if it had the same meaning. The current rate model's anatomical weights remain fixed. These changes improve the training signal, not evidence that the connectome has learned Dota strategy.

## Live verification

29 tests passed, including regeneration reward caps, last-hit/damage scale, reward component validation and game-clock gold accrual without duplicate payments. In the corrected live game, SF gold rose from 602 at game time 2.0 to 619 at 12.0 seconds. Logged feedback includes a real creep-damage reward (+0.00836) and enemy-damage penalties; a new-rule last hit has not yet been observed. This validates plumbing, not improved policy performance.

## lane-v3: XP and rune activation

Actual increases in cumulative hero XP earn +0.001 per XP (+0.10 per 100 XP). Initial XP and repeatedly observing unchanged XP pay nothing. A high-water mark prevents repayment after downward resets. No additional level-up bonus is applied. This is deliberately much smaller than last-hit credit.

A real `dota_rune_activated_server` event for SF's player earns +0.20, with same-type duplicate events within one second suppressed. This rewards activation, not both bottling and activation. The current neural vocabulary has no explicit rune pickup action or rune observations yet; this hook alone does not establish autonomous rune collection. Event fields come from [ModDota's generated declarations](https://github.com/ModDota/TypeScriptDeclarations/blob/master/packages/dota-lua-types/types/events.generated.d.ts).

## Shared-v5 additions

Power Treads, Mask of Madness, Dragon Lance, BKB, Silver Edge, Satanic, Daedalus
and Butterfly each pay +0.20 once per match. Components and repeat purchases do
not repay it. This is human build knowledge; compare a no-guide-reward ablation.
Activation itself pays nothing. Rune pickup/observations, talents and TP are now
available actions, though successful autonomous use is not yet verified.

Jungle creeps receive the same capped +0.10 damage and +1 last-hit reward as lane
creeps. Actual raze casts with no attributed damage within 0.8 seconds cost -0.05;
Requiem uses four seconds and -0.20. This may discourage useful zoning/fear.

Spell outcome tracking tolerates damage arriving up to 0.15 seconds before its
cast notification; old hits and other razes cannot cancel a miss penalty. Only
actual positive enemy damage marks a hit. Raze/ultimate damage now has its own
dashboard label, using the same per-target damage budgets: no extra per-keypress
or duplicate hit bonus. A last hit still adds +1, hero kill +3. A hit on an exhausted
damage budget avoids a miss penalty but does not replenish damage reward.

Actual winners receive +100, losers -100; timeout draws get zero outcome bonus.
Shared transport clips to [-200,200]; PPO scales all reward by 0.1 internally.
These are learning rewards, not extra game XP. A finite win bonus does not ensure
it dominates unlimited farming rewards: evaluate wins. End-to-end full-game
terminal credit/restart and all new action effects still need live verification.
