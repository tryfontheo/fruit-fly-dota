from pathlib import Path
from lupa import LuaRuntime

def test_lane_start_uses_only_living_allied_creeps_and_stays_behind_front():
    lua=LuaRuntime()
    lua.execute('''
      local mt={}
      function Vector(x,y,z)
        return setmetatable({x=x,y=y,z=z,
          Length2D=function(s) return math.sqrt(s.x*s.x+s.y*s.y) end,
          Normalized=function(s) local n=s:Length2D();return Vector(s.x/math.max(1,n),s.y/math.max(1,n),0) end},mt)
      end
      mt.__sub=function(a,b) return Vector(a.x-b.x,a.y-b.y,0) end
      mt.__add=function(a,b) return Vector(a.x+b.x,a.y+b.y,0) end
      mt.__mul=function(a,b) return Vector(a.x*b,a.y*b,0) end
      function creep(x,team,alive) return {GetAbsOrigin=function() return Vector(x,0,0) end,GetTeamNumber=function() return team end,IsAlive=function() return alive end} end
      creeps={creep(9000,3,true),creep(8000,2,false),creep(2000,2,true),creep(1000,2,true)}
      hero={GetTeamNumber=function() return 2 end}
    ''')
    module=lua.execute(Path('dota/live/scripts/vscripts/lane_start.lua').read_text())
    g=lua.globals();base=g.Vector(0,0,0)
    assert module.position(g.hero,g.creeps,base)['x']==1600
    assert module.position(g.hero,lua.table(),base) is None
