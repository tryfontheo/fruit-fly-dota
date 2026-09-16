-- Training initial-state curriculum only, never a tactical movement policy.
local M={}
function M.position(hero,creeps,base,towers)
  local best=nil;local farthest=-1
  for _,u in ipairs(creeps) do
    if u:IsAlive() and u:GetTeamNumber()==hero:GetTeamNumber() then
      local distance=(u:GetAbsOrigin()-base):Length2D()
      local front=u:GetAbsOrigin()
      local candidate=front+(base-front):Normalized()*400
      local safe=true
      for _,tower in ipairs(towers or {}) do
        if tower:IsAlive() and tower:GetTeamNumber()~=hero:GetTeamNumber()
          and (tower:GetAbsOrigin()-candidate):Length2D()<tower:Script_GetAttackRange()+300 then safe=false;break end
      end
      if safe and distance>farthest then best=u;farthest=distance end
    end
  end
  if not best then return nil end
  local front=best:GetAbsOrigin();local back=base-front
  return front+back:Normalized()*400
end
return M
