import numpy as np
import pytest
from scipy.sparse import csr_matrix
from fruit_fly_dota.full_neural import FullReservoir
from fruit_fly_dota.live import Controller, validate

def payload(seq=0):
    return dict(seq=seq, obs=[.1]*16, legal=[1]*13)

def test_signal_must_cross_anatomical_edges():
    w=csr_matrix(([1.,1.],([1,2],[0,1])),shape=(3,3))
    brain=FullReservoir(w,[0],[2],input_size=16,pools=1)
    assert abs(brain.features(np.ones(16))[0])>0
    disconnected=FullReservoir(w*0,[0],[2],input_size=16,pools=1)
    assert disconnected.features(np.ones(16))[0]==0
    brain.reset()
    assert not brain.state.any()

@pytest.mark.parametrize('field,value', [('seq',True),('seq',-1),('obs',[float('nan')]*16),('obs',[0]*15),('legal',[1]*12),('legal',[0]*13)])
def test_invalid_protocol(field,value):
    p=payload(); p[field]=value
    with pytest.raises(ValueError): validate(p)

def test_legal_mask_and_sequence():
    brain=FullReservoir(csr_matrix(([1.],([1],[0])),shape=(2,2)),[0],[1],input_size=16,pools=1)
    c=Controller(brain)
    p=payload(1); p['legal']=[1]+[0]*12
    assert c.step(p)['action']==0
    with pytest.raises(ValueError): c.step(p)

def test_live_lua_compiles():
    from pathlib import Path
    from lupa import LuaRuntime
    lua=LuaRuntime()
    # Compiles/defines functions; engine API execution is tested in the real client.
    lua.execute(Path('dota/live/scripts/vscripts/addon_game_mode.lua').read_text())
