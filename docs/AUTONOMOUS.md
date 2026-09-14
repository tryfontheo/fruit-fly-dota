# Independent local training

Double-click **Start-Training.cmd** to install the project addon, start the local neural learner and launch Dota into automatic practice without Codex. If Dota is already open, load the project addon once; the launcher does not interrupt another game. It checks for an existing controller, saves every 25 decisions using atomic replacement, restores its own v3 checkpoint on restart, and restarts a failed worker after five seconds. Files are under `work/autonomous-v3*`; keep these files to retain learning. The computer must stay awake. This does not automatically recover Dota crashes; run the launcher again if the game closes.

Install with `scripts/install_dota.ps1`, launch the local Workshop addon with `scripts/launch_dota.ps1`, then in VConsole run `fly_start`, wait for the hero, and run `fly_train`. This starts repeated 90-second practice rounds (or ends a round on death), restores health/mana, places SF near three enemy creeps, and follows him with the camera. `fly_stop` stops hero control and training rounds. `fly_start` resumes ordinary map control; `fly_match` requests other bots.

The environment resets position and enemies; **it never selects SF's tactical actions**. Character XP, items and skill upgrades persist between rounds, so these are continuing practice rounds, not independent evaluation episodes. Normal map units remain present. Returns across changing levels do not prove improved skill. This is not yet a verified autonomous full bot-match curriculum.

The requested rate defaults to 10 decisions/second (600 decisions/minute maximum); `fly_rate 20` requests 20. Actual throughput depends on the full connectome computation and game transport. Cast points/channeling remain protected. Decisions are not equivalent to meaningful APM. Readout eligibility uses elapsed time so increasing frequency does not arbitrarily shrink its memory window.

Actions now include **Frenzy (R)** separately from **Requiem (Y)**, three razes, movement, attacks, four upgrade choices and seven purchase choices. The vocabulary still omits many normal-player actions, items, courier, targeting choices and talent choices. Legality and nearest-visible-target selection are engineered scaffolding. There is no scripted route, retreat, shopping priority or skill build.

Rewards include last hits, kills, objectives, deaths and damage taken (tower damage costs more). This is engineered reward modulation of a readout using fixed MaleCNS connectivity-derived rate dynamics, not biological dopamine simulation or synaptic learning throughout the fly brain. The dashboard shows live rewards, update count and rounds; these establish that learning updates happen, not that good Dota play has emerged.

The v3 26-action schema starts a separate checkpoint because the previous 25-action decoder is incompatible. Previous files are preserved. Pro replay imitation checkpoints remain separate and have not been retrained for this vocabulary. No public/ranked matchmaking is used.

## Local verification — September 13, 2026

26 tests passed. Real Dota automatically started SF, spawned practice enemies, issued neural movement/attack/upgrade orders, applied damage/death feedback, and completed an automatic reset after death. At the first reset the learner had 58 reward updates and cumulative reward -5.6654; negative return is not successful play. Killing only the project learner worker demonstrated supervisor restart and recovery of the saved 58 updates and round count. Observed throughput was about 5 decisions/second at a requested 10 Hz. Frenzy is wired and compiled but an actual Frenzy cast was not observed in this initial run.

Reward tuning and economy update: see [lane-v2 reward design](REWARDS.md). Passive gold is explicitly 100 GPM; idle punishment is removed, creep damage has a capped +0.10 budget, and last hits earn +1.00. Reward-version tags distinguish these runs from the initial verification above.
