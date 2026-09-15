-- Allied lane creeps are visible on the team's minimap. No chosen route/order.
local M={}
function M.append(h,obs)
  local pos=h:GetAbsOrigin();local nearest=nil;local distance=math.huge
  for _,u in ipairs(Entities:FindAllByClassname("npc_dota_creep_lane")) do
    if u:IsAlive() and u:GetTeamNumber()==h:GetTeamNumber() then
      local d=(u:GetAbsOrigin()-pos):Length2D()
      if d<distance then nearest=u;distance=d end
    end
  end
  local delta=nearest and nearest:GetAbsOrigin()-pos or Vector(0,0,0)
  table.insert(obs,delta.x/16384);table.insert(obs,delta.y/16384)
  table.insert(obs,nearest and 1 or 0)
  table.insert(obs,h:GetTeamNumber()==DOTA_TEAM_GOODGUYS and 1 or -1)
end
return M
