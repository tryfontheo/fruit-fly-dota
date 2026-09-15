"""Sparse full-graph rate dynamics with annotated sensory and motor populations."""
import numpy as np
from scipy.sparse import csr_matrix

class FullReservoir:
    def __init__(self,w,sensory,motor,input_size=6,pools=64,seed=0,substeps=4,legacy_input_size=None):
        self.n=w.shape[0]; self.substeps=substeps
        if self.n!=w.shape[1] or not len(sensory) or not len(motor): raise ValueError("Invalid graph/populations")
        if np.intersect1d(sensory,motor).size: raise ValueError("Sensory/readout overlap is prohibited")
        self.sensory=np.asarray(sensory); self.motor=np.asarray(motor)
        # Sparse normalization: never allocate n x n dense memory.
        self.w=w.astype(np.float32).tocsr(copy=True)
        scales=np.maximum(np.asarray(abs(self.w).sum(axis=1)).ravel(),1)
        self.w.data *= np.repeat(.9/scales,np.diff(self.w.indptr))
        rng=np.random.default_rng(seed)
        base_size=legacy_input_size or input_size
        if not 0<base_size<=input_size:raise ValueError("Invalid legacy input size")
        self.encoder=rng.normal(0,1.5,(len(sensory),base_size)).astype(np.float32)
        self.bias=rng.normal(0,.5,len(sensory)).astype(np.float32)
        if base_size<input_size:
            extra=np.random.default_rng(seed+1).normal(0,1.5,(len(sensory),input_size-base_size)).astype(np.float32)
            self.encoder=np.column_stack((self.encoder,extra))
        # Mean pools are fixed engineered decoding, not anatomical motor semantics.
        grouping=np.arange(len(motor))%pools
        sizes=np.bincount(grouping,minlength=pools)
        self.pool=csr_matrix((1/np.maximum(1,sizes[grouping]),(grouping,np.arange(len(motor)))),shape=(pools,len(motor)))
        self.feature_size=pools+1
        self.reset()

    def reset(self): self.state=np.zeros(self.n,dtype=np.float32)

    def features(self,observation):
        x=observation.vector() if hasattr(observation,"vector") else np.asarray(observation,dtype=np.float32)
        if x.shape!=(self.encoder.shape[1],) or not np.isfinite(x).all(): raise ValueError("Invalid observation")
        drive=self.encoder@x+self.bias
        for _ in range(self.substeps):
            current=self.w@self.state
            current[self.sensory]+=drive
            self.state=.25*self.state+.75*np.tanh(current)
        return np.append(self.pool@self.state[self.motor],1.)
