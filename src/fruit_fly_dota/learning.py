"""Engineered linear readout: behavior cloning and episodic policy-gradient RL."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax, logsumexp
from .lane import Lane, teacher

class Policy:
    def __init__(self, brain):
        self.brain = brain
        self.weights = np.zeros((brain.n//2 + 1, 4))
        self.scale = np.ones(brain.n//2 + 1)

    def reset(self):
        self.brain.reset()

    def features(self, obs):
        return self.brain.features(obs) / self.scale

    def action(self, obs):
        return int(np.argmax(self.features(obs) @ self.weights))

def demonstrations(policy, episodes=300, seed=1000):
    rng = np.random.default_rng(seed)
    xs, ys = [], []
    for i in range(episodes):
        env = Lane()
        obs = env.reset(seed+i)
        policy.reset()
        while not env.done:
            xs.append(policy.brain.features(obs))
            a = int(teacher(obs))
            ys.append(a)
            # Some off-teacher states without querying a learned policy.
            executed = int(rng.integers(4)) if rng.random() < .12 else a
            obs, _, _, _ = env.step(executed)
    return np.array(xs), np.array(ys)

def clone(policy, x, y):
    policy.scale = np.maximum(x.std(axis=0), .03)
    policy.scale[-1] = 1
    x = x / policy.scale
    target = np.eye(4)[y]
    def loss(flat):
        w = flat.reshape(policy.weights.shape)
        logits = x @ w
        probs = softmax(logits, axis=1)
        penalty = 1e-4
        value = np.mean(logsumexp(logits, axis=1) - logits[np.arange(len(y)), y]) + penalty*np.sum(w*w)/2
        grad = x.T @ (probs-target)/len(y) + penalty*w
        return value, grad.ravel()
    result = minimize(loss, policy.weights.ravel(), method="L-BFGS-B", jac=True, options={"maxiter":250})
    policy.weights = result.x.reshape(policy.weights.shape)
    return dict(loss=float(result.fun), iterations=int(result.nit), converged=bool(result.success), message=str(result.message))

def reinforce(policy, episodes=300, seed=20000, lr=.002):
    """REINFORCE, discounted returns, running scalar baseline; no teacher."""
    rng = np.random.default_rng(seed)
    baseline = 0.
    rewards = []
    for i in range(episodes):
        env = Lane()
        obs = env.reset(seed+i)
        policy.reset()
        trajectory = []
        while not env.done:
            x = policy.features(obs)
            probs = softmax(x @ policy.weights)
            a = int(rng.choice(4, p=probs))
            obs, reward, _, _ = env.step(a)
            trajectory.append((x, probs, a, reward))
        g, grad = 0., np.zeros_like(policy.weights)
        for x, probs, a, reward in reversed(trajectory):
            g = reward + .99*g
            score = np.eye(4)[a] - probs
            grad += np.outer(x, score)*(g-baseline)
        grad /= len(trajectory)
        norm = np.linalg.norm(grad)
        policy.weights += lr*grad/max(1., norm/5.)
        total = sum(t[3] for t in trajectory)
        baseline = .95*baseline + .05*total
        rewards.append(total)
    return dict(episodes=episodes, first_50_mean=float(np.mean(rewards[:50])), last_50_mean=float(np.mean(rewards[-50:])), rewards=rewards)

def evaluate(policy, seeds, mode="policy"):
    records = []
    for seed in seeds:
        env = Lane()
        obs = env.reset(seed)
        policy.reset()
        rng = np.random.default_rng(seed+99999)
        total = 0.
        while not env.done:
            action = int(rng.integers(4)) if mode == "random" else int(teacher(obs)) if mode == "teacher" else policy.action(obs)
            obs, reward, _, _ = env.step(action)
            total += reward
        records.append(dict(seed=int(seed), reward=total, **env.metrics()))
    p = float(np.mean([r["last_hit"] for r in records]))
    n = len(records)
    z = 1.96
    center = (p+z*z/(2*n))/(1+z*z/n)
    half = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return dict(last_hit_rate=p, ci95_wilson=[center-half,center+half], episodes=n,
        invalid_actions_per_episode=float(np.mean([r["invalid_actions"] for r in records])),
        mean_reward=float(np.mean([r["reward"] for r in records])), records=records)
