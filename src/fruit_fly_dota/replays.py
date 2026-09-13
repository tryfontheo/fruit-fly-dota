"""Validated interchange loader; not a .dem decoder or inferred click extractor."""
import json
from .observation import Observation
from .actions import validate

def load_episodes(path):
    episodes = {}
    last_tick = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row.get("schema") != "fly-dota-demo-v1" or row.get("perspective") != "player_visible":
                raise ValueError("Require schema and player-visible perspective")
            if row.get("action_source") not in {"recorded_order", "human_label", "synthetic_teacher"}:
                raise ValueError("Unknown action provenance; state changes are not clicks")
            episode = str(row["episode"])
            tick = int(row["tick"])
            if tick <= last_tick.get(episode, -1):
                raise ValueError("Non-increasing ticks")
            obs = Observation(**row["observation"])
            import numpy as np
            if not np.isfinite(obs.vector()).all():
                raise ValueError("Nonfinite observation")
            episodes.setdefault(episode, []).append((obs, int(validate(row["action"]))))
            last_tick[episode] = tick
    if not episodes:
        raise ValueError("No demonstrations")
    return episodes
