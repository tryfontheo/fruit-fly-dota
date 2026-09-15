-- Engineered training rewards, not biological dopamine concentrations.
local M={version="lane-v3",last_hit=1,deny=.3,hero_kill=3,building_kill=5,death=-3,
  damage_budgets={creep=.1,hero=.5,building=1}}
function M.damage_taken(damage,max_health,tower)
  local fraction=math.min(1,math.max(0,tonumber(damage) or 0)/math.max(1,max_health))
  return -fraction*(tower and 4 or 2)
end
function M.damage_dealt(ledger,target,damage,max_health,kind)
  local budget=M.damage_budgets[kind]
  if not budget then return 0 end
  -- At most one full-health budget per unit lifetime, even if it regenerates.
  -- Entity handles (not reused integer indexes) distinguish newly spawned units.
  local credited=ledger[target] or 0
  local fraction=math.min(1-credited,math.max(0,tonumber(damage) or 0)/math.max(1,max_health))
  ledger[target]=credited+fraction
  return fraction*budget
end
function M.experience(previous,current)
  if previous==nil then return current,0 end
  -- A high-water mark prevents repeated payment after a downward XP reset.
  return math.max(previous,current),math.max(0,current-previous)*.001
end
return M
