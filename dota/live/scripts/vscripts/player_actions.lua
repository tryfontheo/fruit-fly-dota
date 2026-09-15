-- Mechanical action vocabulary only. No build order or action priorities.
local M={skills={"nevermore_shadowraze1","nevermore_dark_lord","nevermore_frenzy","nevermore_requiem"},
items={"item_boots","item_gloves","item_boots_of_elves","item_lifesteal","item_broadsword","item_blade_of_alacrity","item_recipe_yasha"}}
function M.can_buy(h,name)
  local spawn=Entities:FindByClassname(nil,h:GetTeamNumber()==DOTA_TEAM_GOODGUYS and "info_player_start_goodguys" or "info_player_start_badguys")
  if not spawn or (h:GetAbsOrigin()-spawn:GetAbsOrigin()):Length2D()>1100 then return false end
  local free=false
  for i=0,5 do if not h:GetItemInSlot(i) then free=true end end
  return free and GetItemCost(name)>0 and h:GetGold()>=GetItemCost(name)
end
function M.append_legal(h,legal)
  for _,name in ipairs(M.skills) do
    local a=h:FindAbilityByName(name)
    table.insert(legal,h:GetAbilityPoints()>0 and a and a:CanAbilityBeUpgraded()==ABILITY_CAN_BE_UPGRADED and 1 or 0)
  end
  for _,name in ipairs(M.items) do table.insert(legal,M.can_buy(h,name) and 1 or 0) end
end
function M.append_observation(h,obs)
  for _,name in ipairs(M.skills) do
    local a=h:FindAbilityByName(name)
    table.insert(obs,a and a:GetLevel()/4 or 0)
  end
  for _,name in ipairs(M.items) do
    local count=0
    for slot=0,8 do local item=h:GetItemInSlot(slot);if item and item:GetAbilityName()==name then count=count+1 end end
    table.insert(obs,count/9)
  end
end
function M.apply(h,action)
  if action>=14 and action<=17 then
    local a=h:FindAbilityByName(M.skills[action-13])
    if a and h:GetAbilityPoints()>0 and a:CanAbilityBeUpgraded()==ABILITY_CAN_BE_UPGRADED then
      h:UpgradeAbility(a);print("FLY_NEURAL_UPGRADE",a:GetAbilityName());return true
    end
  elseif action>=18 and action<=24 then
    local name=M.items[action-17]
    if M.can_buy(h,name) then
      local cost=GetItemCost(name)
      local item=h:AddItemByName(name)
      if item then h:SpendGold(cost,DOTA_ModifyGold_PurchaseItem);print("FLY_NEURAL_PURCHASE",name,cost);return true end
    end
  end
  return false
end
return M
