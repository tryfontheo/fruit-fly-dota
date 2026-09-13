"""Phenomenological leaky signed-rate reservoir. No claims of biophysical fidelity."""
import numpy as np
from scipy.sparse import csr_matrix

class Reservoir:
    def __init__(self, weights, seed=0, ablation="intact", memory="native"):
        if ablation not in {"intact", "zero", "shuffle"} or memory not in {"native", "reset", "engineered"}:
            raise ValueError("Unknown ablation")
        self.n = weights.shape[0]
        self.memory = memory
        rng = np.random.default_rng(seed)
        w = weights.toarray().astype(float)
        if ablation == "zero":
            w[:] = 0
        elif ablation == "shuffle":
            # Permute destinations per presynaptic neuron: preserves outgoing
            # weight multiset and sign, but not incoming degree or motifs.
            for j in range(self.n):
                w[:, j] = rng.permutation(w[:, j])
        scale = np.maximum(np.abs(w).sum(axis=1), 1)
        self.w = csr_matrix(.9 * w / scale[:, None])
        # Arbitrary engineered population interface. Only first half stimulated;
        # only second half read. There is no observation-to-action bypass.
        rng = np.random.default_rng(seed + 100)
        self.encoder = np.zeros((self.n, 12 if memory == "engineered" else 6))
        self.encoder[:self.n//2] = rng.normal(0, 1.5, (self.n//2, self.encoder.shape[1]))
        self.bias = np.zeros(self.n)
        self.bias[:self.n//2] = rng.normal(0, .5, self.n//2)
        self.reset()

    def reset(self):
        self.state = np.zeros(self.n)
        self.previous = np.zeros(6)

    def features(self, obs):
        x = obs.vector()
        if self.memory == "reset":
            self.state[:] = 0
        if self.memory == "engineered":
            x = np.concatenate([x, self.previous])
        self.previous = obs.vector()
        drive = self.encoder @ x + self.bias
        for _ in range(4):
            self.state = .25*self.state + .75*np.tanh(self.w @ self.state + drive)
        return np.append(self.state[self.n//2:], 1.)
