from pathlib import Path
from lupa import LuaRuntime

def test_tp_home_rejects_nearby_and_rechecks_before_execution():
    lua=LuaRuntime()
    lua.execute('''
      distance=0;muted=false;ready=true;orders=0
      local pos=setmetatable({}, {__sub=function() return {Length2D=function() return distance end} end})
      h={GetAbsOrigin=function() return pos end,IsMuted=function() return muted end,entindex=function() return 1 end}
      tp={IsFullyCastable=function() return ready end,entindex=function() return 2 end}
      base={GetAbsOrigin=function() return pos end}
      function ExecuteOrderFromTable(order) orders=orders+1 end
      DOTA_UNIT_ORDER_CAST_POSITION=5
    ''')
    m=lua.execute(Path('dota/live/scripts/vscripts/interactions.lua').read_text())
    g=lua.globals();context=lua.table(tp=g.tp,base=g.base)
    for distance in (0,1100,1600):
        g.distance=distance
        assert not m.can_tp_home(g.h,g.tp,g.base)
        assert not m.apply(g.h,52,context)
    assert g.orders==0
    g.distance=1601
    assert m.can_tp_home(g.h,g.tp,g.base)
    assert m.apply(g.h,52,context) and g.orders==1
    g.muted=True
    assert not m.apply(g.h,52,context)
    g.muted=False;g.ready=False
    assert not m.apply(g.h,52,context)
    assert not m.can_tp_home(g.h,None,g.base)
