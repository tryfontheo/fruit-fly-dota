-- User-selected item checklist, no buying priority or tactical activation logic.
local M={items={"item_power_treads","item_mask_of_madness","item_dragon_lance","item_black_king_bar","item_silver_edge","item_satanic","item_greater_crit","item_butterfly"},
actives={"item_mask_of_madness","item_black_king_bar","item_silver_edge","item_satanic","item_power_treads"}}
function M.find(h,name)
  for slot=0,5 do local item=h:GetItemInSlot(slot);if item and item:GetAbilityName()==name then return item end end
end
function M.claim(seen,name)
  for _,wanted in ipairs(M.items) do
    if name==wanted and not seen[name] then seen[name]=true;return .2 end
  end
  return 0
end
function M.observe(h,obs,legal,playerActions)
  for _,name in ipairs(M.items) do
    table.insert(obs,M.find(h,name) and 1 or 0)
    table.insert(legal,playerActions.can_buy(h,name) and 1 or 0)
  end
  for _,name in ipairs(M.actives) do
    local item=M.find(h,name)
    local ready=item and item:IsFullyCastable() and not h:IsMuted()
    table.insert(obs,ready and 1 or 0);table.insert(legal,ready and 1 or 0)
  end
end
function M.apply(h,action,playerActions)
  if action>=26 and action<=33 then
    local name=M.items[action-25]
    if not playerActions.can_buy(h,name) then return false end
    local cost=GetItemCost(name)
    local item=h:AddItemByName(name)
    if not item then return false end
    h:SpendGold(cost,DOTA_ModifyGold_PurchaseItem)
    print("FLY_GUIDE_PURCHASE",name,cost);return true
  end
  if action>=34 and action<=38 then
    local name=M.actives[action-33];local item=M.find(h,name)
    if not item or not item:IsFullyCastable() or h:IsMuted() then return false end
    ExecuteOrderFromTable({UnitIndex=h:entindex(),OrderType=DOTA_UNIT_ORDER_CAST_NO_TARGET,AbilityIndex=item:entindex(),Queue=false})
    print("FLY_ITEM_ACTIVE",name);return true
  end
  return false
end
return M
