-- EXPERIMENTAL: not engine-tested. Workshop tools only, no public lobby path.
-- This module only maps validated fixture observations to simple orders.
-- A map/fixture must call FlyLaneStep; see dota/README.md before integration.
local policy = require("fly_policy")
local running = false
function Precache(context) end
function Activate()
  if not IsInToolsMode() then error("fruit-fly-dota requires Workshop Tools") end
  Convars:RegisterCommand("fly_lane_stop", function()
    running = false
    policy.reset()
  end, "Disable lane controller", 0)
end

function FlyLaneReset()
  assert(IsInToolsMode(), "Workshop Tools only")
  policy.reset()
  running = true
end

-- Explicit fixture API, not arbitrary game telemetry. x is the six-element
-- observation.vector() encoding. target must be the one visible fixture creep.
-- stop/wait does not cancel an existing attack; attack is issued only as requested.
function FlyLaneStep(hero, target, x, laneOrigin, laneLength)
  if not IsInToolsMode() or not running then return nil end
  if not hero or hero:IsNull() or not hero:IsAlive() then return nil end
  if #x ~= 6 or laneLength <= 0 then return nil end
  for i=1,6 do if type(x[i]) ~= "number" or x[i] ~= x[i] or math.abs(x[i]) > 10 then return nil end end
  local action = policy.action(x)
  if action == 1 or action == 2 then
    local pos = hero:GetAbsOrigin()
    local dx = (action == 2 and 1 or -1)*.07*laneLength
    local nextX = math.max(laneOrigin.x,math.min(laneOrigin.x+laneLength,pos.x+dx))
    ExecuteOrderFromTable({UnitIndex=hero:entindex(),OrderType=DOTA_UNIT_ORDER_MOVE_TO_POSITION,
      Position=Vector(nextX,laneOrigin.y,pos.z),Queue=false})
  elseif action == 3 and target and not target:IsNull() and target:IsAlive() and hero:CanEntityBeSeenByMyTeam(target) then
    ExecuteOrderFromTable({UnitIndex=hero:entindex(),OrderType=DOTA_UNIT_ORDER_ATTACK_TARGET,
      TargetIndex=target:entindex(),Queue=false})
  end
  return action
end
