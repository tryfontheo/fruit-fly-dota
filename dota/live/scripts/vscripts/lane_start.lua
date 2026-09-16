-- Training initial-state curriculum only, never a tactical movement policy.
local M={}
function M.position(hero,creeps,base)
  local best=nil;local farthest=-1
  for _,u in ipairs(creeps) do
    if u:IsAlive() and u:GetTeamNumber()==hero:GetTeamNumber() then
      local distance=(u:GetAbsOrigin()-base):Length2D()
      if distance>farthest then best=u;farthest=distance end
    end
  end
  if not best then return nil end
  local front=best:GetAbsOrigin();local back=base-front
  return front+back:Normalized()*400
end
return M
