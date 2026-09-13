-- Heavy, explicit engineering baseline. This is NOT learned fly strategy.
-- Neural movement choices select small offsets on an engineered mid-lane route.
local M={index=1,shopping=1,retreat=false}
local route={Vector(-4200,-3600,0),Vector(-1600,-1400,0),Vector(0,0,0),Vector(1500,1400,0),Vector(3500,3200,0),Vector(6000,5500,0)}
local build={"item_boots","item_gloves","item_boots_of_elves","item_lifesteal","item_broadsword","item_blade_of_alacrity","item_boots_of_elves","item_recipe_yasha"}
function M.shop(h)
  -- Explicit custom-shop transaction fallback: basic unlimited-stock items only.
  -- The engine rejected scripted native purchase orders for this local player.
  -- Enforce fountain proximity, price and free inventory space; spend real gold.
  if (h:GetAbsOrigin()-Vector(-6700,-6700,0)):Length2D()>1100 then return end
  local name=build[M.shopping]
  if not name or h:GetGold()<GetItemCost(name) then return end
  local free=false
  for slot=0,5 do if not h:GetItemInSlot(slot) then free=true end end
  if not free then return end
  local cost=GetItemCost(name)
  if cost<=0 then return end
  local item=h:AddItemByName(name)
  if not item then return end
  h:SpendGold(cost,DOTA_ModifyGold_PurchaseItem)
  M.shopping=M.shopping+1
  print("FLY_CUSTOM_SHOP_PAID",name,cost,h:GetGold())
end
function M.move(h,action)
  local p=h:GetAbsOrigin()
  if h:GetHealth()/h:GetMaxHealth()<.3 then M.retreat=true end
  if M.retreat and h:GetHealth()/h:GetMaxHealth()>.95 then M.retreat=false;M.index=1 end
  local goal
  if M.retreat or (M.shopping==1 and h:GetGold()>=GetItemCost(build[1])) then goal=Vector(-6700,-6700,0)
  else
    -- Recover the route after respawning rather than cutting straight through trees.
    if p.x < -5500 and p.y < -5500 then M.index=1 end
    if (p-route[M.index]):Length2D()<600 and M.index<#route then M.index=M.index+1 end
    goal=route[M.index]
  end
  local offset=(action-4)*25
  return {UnitIndex=h:entindex(),OrderType=M.retreat and DOTA_UNIT_ORDER_MOVE_TO_POSITION or DOTA_UNIT_ORDER_ATTACK_MOVE,
          Position=goal+Vector(offset,-offset,0),Queue=false}
end
return M
