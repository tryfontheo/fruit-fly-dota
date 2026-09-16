from pathlib import Path
import pytest
from lupa import LuaRuntime

def tracker():
    lua=LuaRuntime()
    return lua.execute(Path('dota/live/scripts/vscripts/spell_feedback.lua').read_text()).new()

def test_missed_raze_is_penalized_once_after_actual_cast():
    t=tracker();name='nevermore_shadowraze1'
    assert len(t.settle(5))==0
    t.cast(name,10);t.cast(name,10.1)
    assert len(t.settle(10.7))==0
    outcomes=t.settle(10.81)
    assert outcomes[1]['penalty']==pytest.approx(-.05)
    assert len(t.settle(20))==0

@pytest.mark.parametrize('before',[True,False])
def test_damage_before_or_after_cast_event_counts_as_hit(before):
    t=tracker();name='nevermore_shadowraze2'
    if before:t.damage(name,9.99)
    t.cast(name,10)
    if not before:t.damage(name,10.01)
    outcome=t.settle(11)[1]
    assert outcome['hit'] and outcome['penalty']==0

def test_old_damage_and_other_raze_do_not_hide_a_miss():
    t=tracker();t.damage('nevermore_shadowraze1',1)
    t.cast('nevermore_shadowraze1',5);t.damage('nevermore_shadowraze2',5.1)
    assert t.settle(6)[1]['penalty']==pytest.approx(-.05)

def test_ultimate_has_longer_window_and_larger_miss_penalty():
    t=tracker();t.cast('nevermore_requiem',0)
    assert len(t.settle(3.9))==0
    assert t.settle(4.1)[1]['penalty']==pytest.approx(-.2)
