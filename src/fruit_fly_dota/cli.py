import argparse
import json
from pathlib import Path
import numpy as np
from .connectome import prepare, load, sha256
from .neural import Reservoir
from .learning import Policy, demonstrations, clone, reinforce, evaluate
from .evaluation import purity

def main():
    p = argparse.ArgumentParser(description="Toy lane experiments with real connectivity; no matchmaking")
    p.add_argument("command", choices=["prepare", "run", "imitate"])
    p.add_argument("--data", default="data")
    p.add_argument("--output", default="results/run")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--episodes", type=int, default=300)
    p.add_argument("--test-episodes", type=int, default=200)
    p.add_argument("--rl-episodes", type=int, default=300)
    p.add_argument("--ablation", choices=["intact", "zero", "shuffle"], default="intact")
    p.add_argument("--memory", choices=["native", "reset", "engineered"], default="native")
    p.add_argument("--demos", help="Normalized JSONL with known action provenance")
    args = p.parse_args()
    if min(args.episodes, args.test_episodes) < 1 or args.rl_episodes < 0:
        p.error("Episode counts must be positive; RL may be zero")
    if args.command == "prepare":
        print(json.dumps(prepare(args.data), indent=2))
        return
    weights, manifest = load(args.data)
    policy = Policy(Reservoir(weights, args.seed, args.ablation, args.memory))
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    # Nonoverlapping seeds, common held-out tasks across policy seeds.
    test_seeds = list(range(900000, 900000+args.test_episodes))
    validation_seeds = list(range(800000,800100))
    before = evaluate(policy, test_seeds)
    if args.command == "imitate":
        if not args.demos:
            p.error("imitate requires --demos")
        from .replays import load_episodes
        xs, ys = [], []
        for episode in load_episodes(args.demos).values():
            policy.reset()
            for obs, action in episode:
                xs.append(policy.brain.features(obs)); ys.append(action)
        x,y = np.array(xs),np.array(ys)
        source = {"path":args.demos,"sha256":sha256(args.demos)}
    else:
        x,y = demonstrations(policy, args.episodes, 1000+args.seed*10000)
        source = "synthetic teacher in toy lane, not human replay data"
    fit = clone(policy,x,y)
    bc = evaluate(policy,test_seeds)
    np.savez(output/"bc_policy.npz",weights=policy.weights,scale=policy.scale)
    candidate_before = evaluate(policy, validation_seeds)["mean_reward"]
    backup = policy.weights.copy()
    rl = reinforce(policy,args.rl_episodes,seed=100000+args.seed*10000) if args.rl_episodes else None
    candidate_after = evaluate(policy,validation_seeds)["mean_reward"]
    accepted = candidate_after > candidate_before
    rl_test = evaluate(policy,test_seeds)
    if not accepted:
        policy.weights = backup
    final = evaluate(policy,test_seeds)
    np.savez(output/"policy.npz",weights=policy.weights,scale=policy.scale)
    # Fixed-readout intervention; never refit on held-out outcomes.
    lesion = Policy(Reservoir(weights,args.seed,"zero",args.memory))
    lesion.weights,lesion.scale = policy.weights.copy(),policy.scale.copy()
    result = dict(config=vars(args),connectome=manifest,demonstration_source=source,fit=fit,
        purity=purity(manifest,args.memory,args.ablation),untrained=before,behavior_cloned=bc,
        rl_training=rl,rl_candidate_test=rl_test,rl_accepted_on_validation=accepted,
        validation_before=candidate_before,validation_after=candidate_after,final=final,
        zero_connectivity_lesion=evaluate(lesion,test_seeds),random=evaluate(policy,test_seeds,"random"),
        scripted_teacher=evaluate(policy,test_seeds,"teacher"),
        dota_rank=None,rank_status="Uncalibrated toy task; no Dota rank or MMR inference")
    (output/"metrics.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    (output/"policy_config.json").write_text(json.dumps(dict(seed=args.seed,ablation=args.ablation,memory=args.memory,connectome_sha256=manifest["weights_sha256"]),indent=2))
    print(json.dumps({k:result[k] for k in ["fit","purity","rl_accepted_on_validation","dota_rank"]},indent=2))
    for k in ["untrained","behavior_cloned","rl_candidate_test","final","zero_connectivity_lesion","random","scripted_teacher"]:
        print(k,result[k]["last_hit_rate"])

if __name__ == "__main__":
    main()
