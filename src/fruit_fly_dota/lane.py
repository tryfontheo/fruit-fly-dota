"""One-dimensional toy lane, NOT the Dota engine or calibrated Dota physics."""
import numpy as np
from .actions import Action, validate
from .observation import Observation

class Lane:
    range = .13
    speed = .07
    damage = 24
    max_steps = 80

    def reset(self, seed):
        self.rng = np.random.default_rng(seed)
        self.x = float(self.rng.uniform(.05, .95))
        self.target = float(self.rng.uniform(.2, .8))
        self.hp = float(self.rng.uniform(65, 100))
        self.decay = float(self.rng.uniform(1.0, 2.0))
        self.cooldown = self.windup = self.t = self.invalid = self.attacks = 0
        self.last_hit = False
        self.done = False
        return self.observe()

    def observe(self):
        return Observation(self.x, self.target, max(0, self.hp), self.cooldown, self.windup)

    def step(self, action):
        action = validate(action)
        if self.done:
            raise RuntimeError("Reset a terminated episode")
        reward = -.001
        self.t += 1
        self.cooldown = max(0, self.cooldown - 1)
        if self.windup:
            self.windup -= 1
            if self.windup == 0 and abs(self.x-self.target) <= self.range:
                self.hp -= self.damage
                if self.hp <= 0:
                    self.last_hit = self.done = True
                    reward += 1
        if not self.done:
            if action in (Action.LEFT, Action.RIGHT):
                self.windup = 0  # movement cancels attack preparation
                self.x = float(np.clip(self.x + self.speed * (1 if action == Action.RIGHT else -1), 0, 1))
            elif action == Action.ATTACK:
                if self.cooldown == 0 and self.windup == 0 and abs(self.x-self.target) <= self.range:
                    self.windup, self.cooldown = 2, 8
                    self.attacks += 1
                else:
                    self.invalid += 1
                    reward -= .01
            self.hp -= self.decay
            if self.hp <= 0:
                self.done = True
                reward -= .2
        self.done = self.done or self.t >= self.max_steps
        return self.observe(), reward, self.done, self.metrics()

    def metrics(self):
        return dict(last_hit=int(self.last_hit), steps=self.t, invalid_actions=self.invalid, attacks=self.attacks)

def teacher(obs):
    """Engineered demonstration policy. Never called by learned inference."""
    if not obs.visible:
        return Action.WAIT
    dx = obs.target_x - obs.hero_x
    if abs(dx) > Lane.range:
        return Action.RIGHT if dx > 0 else Action.LEFT
    if obs.cooldown == 0 and obs.windup == 0 and obs.target_hp <= Lane.damage + 2:
        return Action.ATTACK
    return Action.WAIT
