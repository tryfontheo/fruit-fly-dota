-- Extra click-equivalent game orders; never a tactical priority policy.
local M={}
-- Curriculum-only grace period; not a learned retreat decision.
local laneGrace=setmetatable({}, {__mode="k"})
function M.lane_placed(h)
  laneGrace[h]=GameRules:GetDOTATime(false,false)+30
end
-- User-requested training constraint, not a Dota engine legality rule.
function M.can_tp_home(h,tp,base)
  if laneGrace[h] and GameRules:GetDOTATime(false,false)<laneGrace[h] then return false end
  return tp~=nil and base~=nil and tp:IsFullyCastable() and not h:IsMuted()
    and (base:GetAbsOrigin()-h:GetAbsOrigin()):Length2D()>1600
end
function M.context(h,units,obs,legal)
  local pos=h:GetAbsOrigin();local rune=nil;local distance=1600
  for _,candidate in ipairs(Entities:FindAllByClassname("dota_item_rune")) do
    local p=candidate:GetAbsOrigin();local d=(p-pos):Length2D()
    if d<distance and IsLocationVisible(h:GetTeamNumber(),p) then rune=candidate;distance=d end
  end
  local delta=rune and rune:GetAbsOrigin()-pos or Vector(0,0,0)
  table.insert(obs,delta.x/1600);table.insert(obs,delta.y/1600);table.insert(obs,rune and 1 or 0)
  table.insert(legal,rune and 1 or 0) -- 39: rune click
  local talents={}
  for i=0,h:GetAbilityCount()-1 do
    local a=h:GetAbilityByIndex(i)
    if a and string.find(a:GetAbilityName(),"special_bonus_",1,true)==1 then table.insert(talents,a) end
  end
  for i=1,8 do
    local a=talents[i];table.insert(obs,a and a:GetLevel() or 0)
    table.insert(legal,a and h:GetAbilityPoints()>0 and a:CanAbilityBeUpgraded()==ABILITY_CAN_BE_UPGRADED and 1 or 0)
  end
  table.insert(legal,1) -- 48: stop
  for i=2,4 do
    local target=units[i]
    if target and not h:CanEntityBeSeenByMyTeam(target) then target=nil end
    local d=target and target:GetAbsOrigin()-pos or Vector(0,0,0)
    table.insert(obs,d.x/1600);table.insert(obs,d.y/1600)
    table.insert(obs,target and target:GetHealth()/math.max(1,target:GetMaxHealth()) or 0)
    table.insert(obs,target and target:IsHero() and 1 or 0);table.insert(obs,target and 1 or 0)
    table.insert(legal,target and 1 or 0) -- 49..51
  end
  local tp=nil
  for i=0,16 do local item=h:GetItemInSlot(i);if item and item:GetAbilityName()=="item_tpscroll" then tp=item;break end end
  local ready=tp and tp:IsFullyCastable() and not h:IsMuted()
  table.insert(obs,tp and 1 or 0);table.insert(obs,ready and 1 or 0)
  local base=Entities:FindByClassname(nil,h:GetTeamNumber()==DOTA_TEAM_GOODGUYS and "info_player_start_goodguys" or "info_player_start_badguys")
  table.insert(legal,M.can_tp_home(h,tp,base) and 1 or 0) -- 52
  table.insert(legal,base and (base:GetAbsOrigin()-pos):Length2D()<1100 and h:GetGold()>=GetItemCost("item_tpscroll") and not tp and 1 or 0)
  return {rune=rune,talents=talents,units=units,tp=tp,base=base}
end
function M.apply(h,a,c)
  local order={UnitIndex=h:entindex(),Queue=false}
  if a==39 then
    if not c.rune or c.rune:IsNull() or not IsLocationVisible(h:GetTeamNumber(),c.rune:GetAbsOrigin()) then return false end
    order.OrderType=DOTA_UNIT_ORDER_PICKUP_RUNE;order.TargetIndex=c.rune:entindex()
  elseif a>=40 and a<=47 then
    local talent=c.talents[a-39]
    if not talent or h:GetAbilityPoints()<1 or talent:CanAbilityBeUpgraded()~=ABILITY_CAN_BE_UPGRADED then return false end
    h:UpgradeAbility(talent);return true
  elseif a==48 then h:Stop();return true
  elseif a>=49 and a<=51 then
    local target=c.units[a-47]
    if not target or target:IsNull() or not target:IsAlive() or not h:CanEntityBeSeenByMyTeam(target) then return false end
    order.OrderType=DOTA_UNIT_ORDER_ATTACK_TARGET;order.TargetIndex=target:entindex()
  elseif a==52 then
    if not M.can_tp_home(h,c.tp,c.base) then return false end
    order.OrderType=DOTA_UNIT_ORDER_CAST_POSITION;order.AbilityIndex=c.tp:entindex();order.Position=c.base:GetAbsOrigin()
  elseif a==53 then
    if not c.base or (c.base:GetAbsOrigin()-h:GetAbsOrigin()):Length2D()>1100 then return false end
    local cost=GetItemCost("item_tpscroll")
    if h:GetGold()<cost then return false end
    local item=h:AddItemByName("item_tpscroll");if not item then return false end
    h:SpendGold(cost,DOTA_ModifyGold_PurchaseItem);return true
  else return false end
  ExecuteOrderFromTable(order);return true
end
return M
