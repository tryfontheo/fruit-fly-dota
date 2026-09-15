from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from lupa import LuaRuntime
from fruit_fly_dota.full_neural import FullReservoir

def test_duplicate_shop_items_blocked_in_inventory_backpack_and_stash():
    lua=LuaRuntime()
    lua.execute('''
      DOTA_TEAM_GOODGUYS=2
      function GetItemCost(name) return 500 end
      delta={Length2D=function() return 0 end}
      pos=setmetatable({}, {__sub=function() return delta end})
      Entities={FindByClassname=function() return {GetAbsOrigin=function() return pos end} end}
      h={slots={},GetTeamNumber=function() return 2 end, GetAbsOrigin=function() return pos end,
         GetGold=function() return 10000 end,GetItemInSlot=function(self,i) return self.slots[i] end}
      function own(slot,name) h.slots[slot]={GetAbilityName=function() return name end} end
    ''')
    shop=lua.execute(Path('dota/live/scripts/vscripts/player_actions.lua').read_text())
    h=lua.globals().h
    assert shop.can_buy(h,'item_power_treads')
    for slot in (0,6,8,10):
        h.slots=lua.table();lua.globals().own(slot,'item_power_treads')
        assert not shop.can_buy(h,'item_power_treads')
    h.slots=lua.table()
    assert not shop.can_buy(h,'item_gloves')
    assert shop.can_buy(h,'item_mask_of_madness')

def test_append_minimap_preserves_existing_encoder_and_features():
    w=csr_matrix(([1.,1.],([2,3],[0,1])),shape=(4,4))
    old=FullReservoir(w,[0,1],[2,3],input_size=74,legacy_input_size=33)
    new=FullReservoir(w,[0,1],[2,3],input_size=78,legacy_input_size=33)
    np.testing.assert_array_equal(old.encoder,new.encoder[:,:74])
    for _ in range(4):
        np.testing.assert_allclose(old.features(np.ones(74)),new.features(np.r_[np.ones(74),np.zeros(4)]),atol=1e-7)

def test_wave_observation_excludes_enemy_and_dead_creeps():
    lua=LuaRuntime()
    lua.execute('''
      DOTA_TEAM_GOODGUYS=2
      local mt={}
      function Vector(x,y,z) return setmetatable({x=x,y=y,z=z,Length2D=function(s) return math.sqrt(s.x*s.x+s.y*s.y) end},mt) end
      mt.__sub=function(a,b) return Vector(a.x-b.x,a.y-b.y,0) end
      function creep(x,team,alive) return {GetAbsOrigin=function() return Vector(x,0,0) end,GetTeamNumber=function() return team end,IsAlive=function() return alive end} end
      Entities={FindAllByClassname=function() return {creep(1,3,true),creep(2,2,false),creep(800,2,true)} end}
      h={GetAbsOrigin=function() return Vector(0,0,0) end,GetTeamNumber=function() return 2 end}
    ''')
    wave=lua.execute(Path('dota/live/scripts/vscripts/wave_observation.lua').read_text())
    obs=lua.table();wave.append(lua.globals().h,obs)
    assert obs[1]==800/16384 and obs[2]==0 and obs[3]==1 and obs[4]==1
