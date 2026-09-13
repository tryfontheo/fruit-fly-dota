# Research audit — September 13, 2026

## The specific FPS presentation

Recovered from the referenced conversation:

- [First Instagram reel](https://www.instagram.com/reel/DdOSBtHgQ8q/)
- [Second Instagram reel](https://www.instagram.com/reel/DdOS6l0gabj/)
- An attached screenshot titled “Simulated Fruit Fly Brain Enters Valorant as Neon
  Main.” Direct image inspection shows Valorant footage, a neural visualization,
  an animated fly on a keyboard and NeuroMechFly/FlyGym credits. The surrounding
  interface also says “Deadlock.” The small attribution appears to read
  `@jetsetwonn` but that transcription and account identity are unverified.

The Instagram pages did not expose usable content to the web tool. Searches for
the distinctive MaleCNS/YOLOv5/Mercy/Masters description, FPS names and apparent
handle did not locate an authenticated creator repository, paper, training logs,
checkpoint or match record. A search surfaced repeated social claims, including
a copypasta repost; repetition is not independent verification. We did not obtain
the full original videos. The screenshot proves what is displayed, not that the
brain controls the footage or that an agent learned the game.

**Verdict: the specific gaming implementation and Masters claim are unverified.**
There is not enough evidence to call the clip authentic or fabricated. Mixed game
labels may reflect a reused interface or a presentation edit; neither explanation
is established. A neural activity panel can be real yet unrelated to policy
decisions. An animated fly touching keys does not establish a biomechanical
control loop. The previous assistant's confident description of YOLOv5,
video pretraining, attention aiming and Masters performance must be treated as
unverified claims, not implementation facts. Its rank estimates for Dota are also
unsupported; this project does not inherit them as predictions.

To authenticate: obtain the creator's exact source link, immutable code revision,
connectome provenance, input/output mapping, training procedure, model checkpoint,
unedited closed-loop recording with synchronized observations/actions, and
evaluations with the connectome silenced or replaced. No source code in this repo
is represented as a reproduction of that FPS creator's code.

## Verified research versus gaming extrapolation

| Source | What is supported | What it does not establish |
|---|---|---|
| [Google Research MaleCNS announcement](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/) and [Janelia portal](https://male-cns.janelia.org/) | September 3, 2026 release; male CNS wiring including brain and nerve cord; announcement reports over 166,000 neurons and 125 million synapses | Learned game skill, physiological parameters for every neuron, memories or consciousness |
| [FlyWire wiring paper](https://doi.org/10.1038/s41586-024-07558-y) and [connectivity data record](https://zenodo.org/records/10676866) | Adult female brain connectome and a public connectivity resource; distinct from MaleCNS | Interchangeable neuron IDs across male/female datasets or full nervous-system physiology |
| [Shiu et al., Nature 2024](https://www.nature.com/articles/s41586-024-07763-9) | Connectome-based computational modeling of sensorimotor processing with biological validation in studied circuits | Evidence for FPS performance or a general game-learning algorithm |
| [Shiu research code](https://github.com/philshiu/Drosophila_brain_model) | Brian2 LIF code, activation/silencing experiments, v630 defaults and v783 data option | Our rate reservoir is not a reproduction of that model |
| [FlyGym / NeuroMechFly v2](https://github.com/NeLy-EPFL/flygym) | A framework for embodied sensorimotor simulation of a fly | A turnkey trained connectome or evidence that a credited FPS video uses its body dynamics |

The exact biological dataset version, proofreading/filtering policy, counted
neurons versus annotated somata, unique directed pairs versus synaptic contacts,
and thresholding all matter. Do not infer counts from a dashboard label or swap
139k brain counts with 166k male-CNS counts.

## Code actually inspected and data used

Pinned [Shiu repository revision](https://github.com/philshiu/Drosophila_brain_model/tree/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960).
Read its README and `model.py`: it uses Brian2 neuron/synapse objects, leak,
synaptic dynamics, refractory period, delay and Poisson stimulation. Our initial
reservoir deliberately uses a simpler, disclosed engineering model; importing
the same connectivity does not reproduce the published physiological results.

Downloaded `Connectivity_783.parquet` and its upstream license directly from that
revision. File size: 100,804,642 bytes. SHA-256:
`efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347`.
The observed schema supplies presynaptic/postsynaptic IDs and indices, connection
counts, inferred sign and signed counts. Original rows and identifiers for the
selected subset are retained. The processed manifest documents all transformations.
No MaleCNS data is used in the current policy.

The [snedea/flybrain repository](https://github.com/snedea/flybrain) is a separate
browser project found during the search. Its README advertises a FlyWire-based
LIF visualization; it is not identified as the supplied FPS implementation, and
its performance/behavior claims were not independently reproduced here.

## Dota tooling decision

[Clarity](https://github.com/skadistats/clarity) is a concrete replay parser with
documented event/entity access and examples. [OpenDota](https://github.com/odota/core)
is an analytics platform that uses parsing. Neither guarantees exact player
orders or observation correctness for a particular demo; those require validation.
See [replay plan](REPLAYS.md).

For control, prefer a private Workshop Tools addon using VScript, verified against
Valve's locally shipped last-hit-trainer code. Native bot scripting is another
possible route but offers less direct fixture control than a custom addon.
Game-state integration/spectator feeds are not a sufficient reset/action/training
API. A desktop keyboard/mouse bridge is unnecessary for this experiment.

The web Valve wiki fetch failed. Local primary-source Lua inspection confirmed
timers, unit creation and order dispatch. [ModDota's API](https://moddota.com/api/)
and [scripting guide](https://moddota.com/scripting-introduction) are supporting
documentation. Exporting inference directly to Lua avoids adding an HTTP bridge
to the first experiment. Installation and engine validation remain unperformed.

## Boundaries of this audit

This is an initial source audit, not an exhaustive review of every viral fly
project. Search failures are not proof that code does not exist. No creator was
contacted. No private accounts, ranked matches, game credentials or footage
downloads were used. The earlier conversation is context, not scientific evidence.
