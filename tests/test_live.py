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

def test_round_terminal_reward_precedes_trace_reset():
    brain=FullReservoir(csr_matrix(([1.],([1],[0])),shape=(2,2)),[0],[1],input_size=OBS_SIZE,pools=1)
    c=Controller(brain,learn=True)
    c.step(payload(0))
    p=payload(1);p.update(reward=-3,round_end=True)
    r=c.step(p)
    assert r['learning_updates']==1
    assert r['rounds']==1 and r['recent_rounds'][0]['reward']==-3
    assert np.any(c.learner.weights)

def test_atomic_checkpoint_contains_action_schema(tmp_path):
    from fruit_fly_dota.live import save_learning
    brain=FullReservoir(csr_matrix(([1.],([1],[0])),shape=(2,2)),[0],[1],input_size=OBS_SIZE,pools=1)
    c=Controller(brain,learn=True);c.step(payload(0))
    path=tmp_path/'test.npz';save_learning(c,path)
    with np.load(path,allow_pickle=False) as saved:
        assert int(saved['action_count'])==ACTION_COUNT
        np.testing.assert_array_equal(saved['decoder'],c.decoder)
    assert not path.with_suffix('.tmp').exists()

def test_damage_shaping_cannot_outpay_last_hit_or_farm_regeneration():
    from pathlib import Path
    from lupa import LuaRuntime
    lua=LuaRuntime();rules=lua.execute(Path('dota/live/scripts/vscripts/reward_rules.lua').read_text())
    ledger=lua.table();target=lua.table()
    total=sum(rules.damage_dealt(ledger,target,100,1000,'creep') for _ in range(100))
    assert total==pytest.approx(.1)
    assert rules.last_hit>=10*total-1e-9
    assert rules.damage_dealt(ledger,target,1000,1000,'creep')==pytest.approx(0)
    assert rules.damage_dealt(ledger,lua.table(),1000,1000,'creep')==pytest.approx(.1)
    assert rules.damage_dealt(ledger,lua.table(),-100,1000,'hero')==0

def test_reward_components_are_logged_and_validated():
    brain=FullReservoir(csr_matrix(([1.],([1],[0])),shape=(2,2)),[0],[1],input_size=OBS_SIZE,pools=1)
    c=Controller(brain,learn=True);p=payload(0)
    p.update(reward=.01,reward_version='lane-v2',reward_components={'creep_damage':.01})
    assert c.step(p)['reward_components']=={'creep_damage':.01}
    p['reward_components']={'creep_damage':float('nan')}
    with pytest.raises(ValueError):c.step(p)

def test_passive_income_uses_game_time_not_decision_count():
    from pathlib import Path
    from lupa import LuaRuntime
    economy=LuaRuntime(unpack_returned_tuples=True).execute(Path('dota/live/scripts/vscripts/economy.lua').read_text())
    previous,amount=economy.advance(None,0)
    assert amount==0
    previous,amount=economy.advance(previous,60)
    assert amount==100
    # Repeated calls at the same game time (including pause) pay nothing.
    for _ in range(100):
        previous,amount=economy.advance(previous,60)
        assert amount==0
    previous,amount=economy.advance(previous,60.6)
    assert amount==1
    previous,amount=economy.advance(previous,0)
    assert previous==0 and amount==0

def test_xp_reward_pays_only_new_experience():
    from pathlib import Path
    from lupa import LuaRuntime
    rules=LuaRuntime(unpack_returned_tuples=True).execute(Path('dota/live/scripts/vscripts/reward_rules.lua').read_text())
    mark,r=rules.experience(None,300);assert r==0
    mark,r=rules.experience(mark,400);assert r==pytest.approx(.1)
    mark,r=rules.experience(mark,400);assert r==0
    mark,r=rules.experience(mark,0);assert r==0
    mark,r=rules.experience(mark,400);assert r==0
    mark,r=rules.experience(mark,500);assert r==pytest.approx(.1)

def test_extended_inputs_preserve_old_neural_features_when_zero():
    w=csr_matrix(([1.],([1],[0])),shape=(2,2))
    old=FullReservoir(w,[0],[1],input_size=33,pools=1)
    new=FullReservoir(w,[0],[1],input_size=46,pools=1,legacy_input_size=33)
    np.testing.assert_array_equal(old.features(np.ones(33)),new.features(np.r_[np.ones(33),np.zeros(13)]))

def test_guide_completion_cannot_be_farmed_by_rebuying():
    from pathlib import Path
    from lupa import LuaRuntime
    lua=LuaRuntime();guide=lua.execute(Path('dota/live/scripts/vscripts/guide_items.lua').read_text())
    seen=lua.table()
    assert guide.claim(seen,'item_power_treads')==pytest.approx(.2)
    assert guide.claim(seen,'item_power_treads')==0
    assert guide.claim(seen,'item_boots')==0
    assert guide.claim(seen,'item_mask_of_madness')==pytest.approx(.2)
