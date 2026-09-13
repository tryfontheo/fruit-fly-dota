import json
import numpy as np
import pytest
from scipy.sparse import csr_matrix
from fruit_fly_dota.neural import Reservoir
from fruit_fly_dota.observation import Observation
from fruit_fly_dota.lane import Lane, teacher
from fruit_fly_dota.connectome import load
from fruit_fly_dota.replays import load_episodes

def test_real_provenance_and_signal_dependence():
    w,m = load("data")
    assert m["selected_neurons"] == 256 and w.nnz > 0
    obs = Observation(.1,.7,40,0,0)
    live,dead = Reservoir(w),Reservoir(w,ablation="zero")
    assert np.linalg.norm(live.features(obs)[:-1]) > 0
    assert np.all(dead.features(obs)[:-1] == 0)

def test_direction_and_native_memory():
    # Synthetic fixture only: pre 0 -> post 2, never experiment data.
    w = csr_matrix(([1.],([2],[0])),shape=(4,4))
    brain = Reservoir(w)
    a,b = Observation(.1,.9,50,0,0),Observation(.9,.1,10,0,0)
    brain.features(a)
    remembered = brain.features(b)
    brain.reset()
    fresh = brain.features(b)
    assert not np.allclose(remembered,fresh)
    brain.reset()
    assert np.allclose(fresh,brain.features(b))

def test_seed_determinism_and_teacher():
    for seed in range(10):
        a,b = Lane(),Lane()
        assert a.reset(seed) == b.reset(seed)
        while not a.done:
            action = teacher(a.observe())
            assert a.step(action) == b.step(action)
        assert a.last_hit
        with pytest.raises(RuntimeError): a.step(0)

def test_attack_windup_and_invalid():
    e = Lane(); e.reset(0)
    e.x,e.target,e.hp,e.decay = .5,.5,25,1
    e.step(3)
    assert not e.last_hit and e.windup == 2
    e.step(0)
    assert not e.last_hit
    e.step(0)
    assert e.last_hit
    e.reset(0)
    with pytest.raises(ValueError): e.step(99)

def test_replay_rejects_omniscient(tmp_path):
    path = tmp_path/'bad.jsonl'
    path.write_text(json.dumps({"schema":"fly-dota-demo-v1","perspective":"spectator"}))
    with pytest.raises(ValueError): load_episodes(path)
