"""Summarize saved experiments without training or selecting checkpoints."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
lines=["# Initial results", "", "All percentages refer to 200 toy lane episodes, not Dota matches.", "",
    "| Run | Cloned | RL candidate | Selected | Graph lesion | 95% interval (selected) |", "|---|---:|---:|---:|---:|---|"]
for name in ["seed0","seed1","seed2","shuffle","zero","reset","engineered"]:
    d=json.loads((root/"results"/name/"metrics.json").read_text())
    values=[d[k]["last_hit_rate"]*100 for k in ["behavior_cloned","rl_candidate_test","final","zero_connectivity_lesion"]]
    ci=d["final"]["ci95_wilson"]
    lines.append(f"| {name} | "+" | ".join(f"{v:.1f}%" for v in values)+f" | {ci[0]*100:.1f}–{ci[1]*100:.1f}% |")
lines += ["", "Random: 17.5%; scripted teacher: 100%; untrained policies: 0%.", "",
    "No demonstrated fly-specific topology or memory benefit. Shuffled wiring matches seed 0, and state reset performs similarly. These are initial controls with limited seeds, not equivalence tests.", "",
    "Only the engineered-memory run accepted RL on validation; all other selected checkpoints retain cloning weights. Nonzero-graph cloning fits reached the fixed 250-iteration limit. See each metrics.json for fit status, validation scores, RL rewards and full episode records.", "",
    "Default Fly Purity: 42/100 (subjective rubric, 256-neuron coverage). Dota rank: uncalibrated/null. No Dota engine run occurred."]
(root/"results"/"SUMMARY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
