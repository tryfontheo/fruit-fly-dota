local M={}
function M.damage_taken(damage,max_health,tower)
  local fraction=math.min(1,math.max(0,tonumber(damage) or 0)/math.max(1,max_health))
  return -fraction*(tower and 4 or 2)
end
return M
