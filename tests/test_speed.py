from pathlib import Path
from lupa import LuaRuntime

def test_speed_respects_latency_ceiling_and_failed_requests():
    control=LuaRuntime().execute(Path('dota/live/scripts/vscripts/speed_control.lua').read_text())
    assert control.recommend(.3,0,4)==4
    assert control.recommend(.6,0,4)==2
    assert control.recommend(.6,0,1)==1
    assert control.recommend(.1,1,4)==1
    assert control.recommend(.1,1,.5)==.5
    assert control.recommend(3,0,4)==.5

def test_governor_uses_wall_clock_and_backs_off_on_failed_requests():
    lua=LuaRuntime()
    lua.execute('''
      ms=0;commands={}
      function GetSystemTimeMS() return ms end
      function IsInToolsMode() return true end
      function SendToServerConsole(s) table.insert(commands,s) end
      Convars={RegisterCommand=function() end,GetFloat=function() return 1 end}
      GameRules={GetGameModeEntity=function() return {SetContextThink=function(_,name,fn) tick=fn end} end}
    ''')
    c=lua.execute(Path('dota/live/scripts/vscripts/speed_control.lua').read_text())
    c.start();g=lua.globals()
    for _ in range(40):c.sample(.5,True)
    g.ms=11000;g.tick();assert c.current==1.5
    for _ in range(40):c.sample(.5,True)
    c.sample(1.5,False)
    g.ms=22000;g.tick();assert c.current==1
