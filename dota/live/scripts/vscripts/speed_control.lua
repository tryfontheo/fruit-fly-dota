-- Local-tools only. Faster simulation must not exceed the learner's response budget.
local M={samples={},failures=0,ceiling=4,current=1}
function M.now() return GetSystemTimeMS()/1000 end
function M.recommend(latency,failures,ceiling)
  if failures>0 then return math.min(1,ceiling) end
  -- At most 1.2 game seconds of p95 command latency; quantize to quarter speeds.
  return math.max(.5,math.min(ceiling,math.floor(1.2/math.max(.05,latency)*4)/4))
end
function M.sample(seconds,ok)
  table.insert(M.samples,seconds)
  if #M.samples>100 then table.remove(M.samples,1) end
  if not ok then M.failures=M.failures+1 end
end
function M.start()
  assert(IsInToolsMode(),"Local tools only")
  SendToServerConsole("sv_cheats 1")
  SendToServerConsole("host_timescale 1")
  Convars:RegisterCommand("fly_speed_max",function(_,value)
    local n=tonumber(value);if n and n>=.5 and n<=4 then M.ceiling=n end
  end,"Automatic speed ceiling 0.5..4",0)
  local last=M.now()
  GameRules:GetGameModeEntity():SetContextThink("FlyAdaptiveSpeed",function()
    if M.now()-last<10 or #M.samples<30 then return 1 end
    last=M.now()
    local sorted={};for i,v in ipairs(M.samples) do sorted[i]=v end;table.sort(sorted)
    local p95=sorted[math.ceil(#sorted*.95)]
    local safe=M.recommend(p95,M.failures,M.ceiling)
    local nextSpeed=math.min(safe,M.current+.5)
    if nextSpeed~=M.current then
      SendToServerConsole("host_timescale "..nextSpeed);M.current=nextSpeed
    end
    print("FLY_SPEED",M.current,"engine",Convars:GetFloat("host_timescale"),"p95_wall",p95,"failures",M.failures)
    M.samples={};M.failures=0
    return 1
  end,1)
end
return M
