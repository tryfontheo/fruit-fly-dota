from pathlib import Path
import pytest
from lupa import LuaRuntime


def test_fountain_cost_grace_recovery_and_game_time_rate():
    lua=LuaRuntime()
    rules=lua.execute(Path('dota/live/scripts/vscripts/reward_rules.lua').read_text())
    state=lua.table()
    for t in (0,5,10,15):
        assert rules.fountain_idle(state,t,True)==0
    assert rules.fountain_idle(state,16,True)==pytest.approx(-.02)
    assert rules.fountain_idle(state,16,True)==0
    assert rules.fountain_idle(state,17,False)==0
    assert rules.fountain_idle(state,18,True)==0
    assert rules.fountain_idle(state,32,True)==0
    assert rules.fountain_idle(state,1000,True)==pytest.approx(-.02)
    for hz in (2,10):
        state=lua.table()
        total=sum(rules.fountain_idle(state,t/hz,True) for t in range(30*hz+1))
        assert total==pytest.approx(-.3)
