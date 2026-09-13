"""Engineered telemetry, normalized without future or teacher information."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Observation:
    hero_x: float
    target_x: float
    target_hp: float
    cooldown: float
    windup: float
    visible: bool = True

    def vector(self):
        return np.array([self.hero_x * 2 - 1,
            (self.target_x * 2 - 1) if self.visible else 0,
            (self.target_hp / 100) if self.visible else 0,
            self.cooldown / 8, self.windup / 2, float(self.visible)], dtype=float)
