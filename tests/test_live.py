import numpy as np
import pytest
from scipy.sparse import csr_matrix
from fruit_fly_dota.full_neural import FullReservoir
from fruit_fly_dota.live import Controller, validate, OBS_SIZE, ACTION_COUNT

def payload(seq=0):
    return dict(seq=seq, obs=[.1]*OBS_SIZE, legal=[1]*ACTION_COUNT)

def test_signal_must_cross_anatomical_edges():
    w=csr_matrix(([1.,1.],([1,2],[0,1])),shape=(3,3))
    brain=FullReservoir(w,[0],[2],input_size=OBS_SIZE,pools=1)
    assert abs(brain.features(np.ones(OBS_SIZE))[0])>0
    disconnected=FullReservoir(w*0,[0],[2],input_size=OBS_SIZE,pools=1)
    assert disconnected.features(np.ones(OBS_SIZE))[0]==0
    brain.reset()
    assert not brain.state.any()

@pytest.mark.parametrize('field,value', [('seq',True),('seq',-1),('obs',[float('nan')]*16),('obs',[0]*15),('legal',[1]*12),('legal',[0]*13)])
def test_invalid_protocol(field,value):
    p=payload(); p[field]=value
    with pytest.raises(ValueError): validate(p)

def test_legal_mask_and_sequence():
    brain=FullReservoir(csr_matrix(([1.],([1],[0])),shape=(2,2)),[0],[1],input_size=OBS_SIZE,pools=1)
    c=Controller(brain)
    p=payload(1); p['legal']=[1]+[0]*(ACTION_COUNT-1)
    assert c.step(p)['action']==0
    with pytest.raises(ValueError): c.step(p)

def test_live_lua_compiles():
    from pathlib import Path
    from lupa import LuaRuntime
    lua=LuaRuntime()
    # Compiles/defines functions; engine API execution is tested in the real client.
    lua.execute(Path('dota/live/scripts/vscripts/addon_game_mode.lua').read_text(encoding='utf-8'))

def test_reward_is_applied_once_to_previous_decision():
    brain=FullReservoir(csr_matrix(([1.],([1],[0])),shape=(2,2)),[0],[1],input_size=OBS_SIZE,pools=1)
    c=Controller(brain,learn=True)
    c.step(payload(0))
    p=payload(1);p['reward']=1
    result=c.step(p)
    assert result['learning_updates']==1
    saved=c.learner.weights.copy()
    with pytest.raises(ValueError):c.step(p)
    np.testing.assert_array_equal(saved,c.learner.weights)

def test_assisted_payload_is_rejected():
    brain=FullReservoir(csr_matrix(([1.],([1],[0])),shape=(2,2)),[0],[1],input_size=OBS_SIZE,pools=1)
    p=payload();p['assisted']=True
    with pytest.raises(ValueError):Controller(brain,learn=True).step(p)

def test_damage_feedback_scaling():
    from pathlib import Path
    from lupa import LuaRuntime
    rules=LuaRuntime().execute(Path('dota/live/scripts/vscripts/reward_rules.lua').read_text())
    assert rules.damage_taken(100,1000,False)==pytest.approx(-.2)
    assert rules.damage_taken(100,1000,True)==pytest.approx(-.4)
    assert rules.damage_taken(-100,1000,True)==0
    assert rules.damage_taken(10000,1000,True)==-4
