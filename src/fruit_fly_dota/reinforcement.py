"""Experimental reward-modulated readout plasticity, not biological dopamine.

Eligibility retains recent policy gradients. Only the engineered decoder learns;
anatomical edges remain fixed. Reward must describe events AFTER the last action.
"""
import numpy as np


class RewardLearner:
    def __init__(self, feature_size, actions, rate=.02, decay=.8):
        self.weights = np.zeros((feature_size, actions))
        self.trace = np.zeros_like(self.weights)
        self.rate, self.decay = rate, decay
        self.total_reward = 0.
        self.updates = 0

    def reset_episode(self):
        self.trace.fill(0)

    def feedback(self, reward):
        if not np.isfinite(reward) or abs(reward) > 20:
            raise ValueError('Invalid reward')
        self.total_reward += reward
        if reward and np.any(self.trace):
            self.weights += self.rate * reward * self.trace
            np.clip(self.weights, -5, 5, out=self.weights)
            self.updates += 1

    def record(self, features, probabilities, action):
        gradient = -probabilities.copy()
        gradient[action] += 1
        # No bias feature: reward adaptation still requires a neural signal.
        x = np.asarray(features).copy(); x[-1] = 0
        x /= max(np.linalg.norm(x), 1e-8)
        self.trace = self.decay * self.trace + np.outer(x, gradient)

    def logits(self, features):
        x = np.asarray(features).copy(); x[-1] = 0
        x /= max(np.linalg.norm(x), 1e-8)
        return x @ self.weights
