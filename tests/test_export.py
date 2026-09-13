import json
from pathlib import Path
import numpy as np
import pytest
from fruit_fly_dota.connectome import load
from fruit_fly_dota.neural import Reservoir
from fruit_fly_dota.learning import Policy
from fruit_fly_dota.lane import Lane

def test_exported_lua_matches_python_actions():
    from lupa import LuaRuntime
    lua = LuaRuntime(unpack_returned_tuples=True)
    mod = lua.execute(Path("dota/addon/scripts/vscripts/fly_policy.lua").read_text())
    w,m = load("data")
    config = json.loads(Path("results/seed0/policy_config.json").read_text())
    p = Policy(Reservoir(w,config["seed"],config["ablation"],config["memory"]))
    checkpoint = np.load("results/seed0/policy.npz",allow_pickle=False)
    p.weights,p.scale = checkpoint["weights"],checkpoint["scale"]
    for seed in range(20):
        env = Lane(); obs = env.reset(seed)
        mod.reset(); p.reset()
        while not env.done:
            expected = p.action(obs)
            assert mod.action(lua.table_from(obs.vector().tolist())) == expected
            obs,_,_,_ = env.step(expected)

def test_corrupted_connectivity_rejected(tmp_path):
    import shutil
    shutil.copytree("data/processed",tmp_path/"processed")
    path=tmp_path/"processed"/"weights.npz"
    path.write_bytes(path.read_bytes()+b"tamper")
    with pytest.raises(ValueError,match="integrity"):
        load(tmp_path)
