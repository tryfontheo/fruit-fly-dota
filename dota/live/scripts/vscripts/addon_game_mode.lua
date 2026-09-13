-- Real map smoke test, UNTRAINED policy. No stock bot controls our hero.
-- All observations, target selection and compass actions are engineered.
local running, pending, seq, generation = false, false, 0, 0
local controlledHero=nil
local function stop()
  running=false; generation=generation+1; pending=false
  local h=controlledHero
  if h then h:Stop() end
  print("FLY_STOP")
end
function Precache(context) PrecacheUnitByNameSync("npc_dota_hero_lina", context) end
function Activate()
  assert(IsInToolsMode(), "Only local Workshop Tools games are supported")
  local mode=GameRules:GetGameModeEntity()
  mode:SetCustomGameForceHero("npc_dota_hero_lina")
  GameRules:SetHeroSelectionTime(0)
  GameRules:SetPreGameTime(0)
  GameRules:SetCustomGameSetupTimeout(0)
  Convars:RegisterCommand("fly_start", function()
    stop()
    local player=PlayerResource:GetPlayer(0)
    if not player then print("FLY_NO_LOCAL_PLAYER"); return end
    if not controlledHero then
      player:SetTeam(DOTA_TEAM_GOODGUYS)
      -- Include player-specific resources before spawning a controllable hero.
      local setupEpoch=generation
      PrecacheUnitByNameAsync("npc_dota_hero_lina",function()
        if setupEpoch~=generation then return end
        controlledHero=CreateUnitByName("npc_dota_hero_lina",Vector(-6500,-6000,256),true,nil,nil,DOTA_TEAM_GOODGUYS)
        controlledHero:SetControllableByPlayer(0,true)
        print("FLY_HERO_READY")
      end,0)
    end
    seq=0; running=true; print("FLY_START_UNTRAINED")
  end, "Enable full-connectome controller", 0)
  Convars:RegisterCommand("fly_stop", stop, "Stop controller and hero", 0)
  mode:SetContextThink("FlyThink", FlyThink, .2)
  print("FLY_ADDON_READY: use fly_start; fly_stop disables control")
end
local directions={{1,0},{.707,.707},{0,1},{-.707,.707},{-1,0},{-.707,-.707},{0,-1},{.707,-.707}}
function FlyThink()
  if not running or not IsInToolsMode() or GameRules:IsGamePaused() then return .2 end
  local h=controlledHero
  if not h or not h:IsAlive() or pending then return .2 end
  local pos=h:GetAbsOrigin()
  local units=FindUnitsInRadius(h:GetTeamNumber(),pos,nil,1600,DOTA_UNIT_TARGET_TEAM_ENEMY,
    DOTA_UNIT_TARGET_HERO+DOTA_UNIT_TARGET_BASIC+DOTA_UNIT_TARGET_BUILDING,
    DOTA_UNIT_TARGET_FLAG_FOW_VISIBLE+DOTA_UNIT_TARGET_FLAG_NO_INVIS,FIND_CLOSEST,false)
  local target=units[1]
  if target and not h:CanEntityBeSeenByMyTeam(target) then target=nil end
  local delta=target and (target:GetAbsOrigin()-pos) or Vector(0,0,0)
  local obs={pos.x/8192,pos.y/8192,h:GetHealth()/h:GetMaxHealth(),h:GetMana()/math.max(1,h:GetMaxMana()),
    h:GetLevel()/30,h:GetGold()/30000,h:Script_GetAttackRange()/2000,GameRules:GetDOTATime(false,false)/7200,
    delta.x/1600,delta.y/1600,target and target:GetHealth()/math.max(1,target:GetMaxHealth()) or 0,
    target and 1 or 0,target and target:IsHero() and 1 or 0,0,0,0}
  local legal={1,1,1,1,1,1,1,1,1,target and 1 or 0,0,0,0}
  local names={"lina_dragon_slave","lina_light_strike_array","lina_laguna_blade"}
  for i,name in ipairs(names) do
    local a=h:FindAbilityByName(name)
    local ready=a and a:GetLevel()>0 and a:IsFullyCastable() and not h:IsSilenced()
    obs[13+i]=ready and 1 or 0
    legal[10+i]=ready and target and delta:Length2D()<=a:GetCastRange(pos,target) and 1 or 0
  end
  local requestSeq=seq; seq=seq+1
  local epoch=generation; local sent=Time(); pending=true
  local req=CreateHTTPRequestScriptVM("POST","http://127.0.0.1:8765/step")
  req:SetHTTPRequestRawPostBody("application/json",'{"seq":'..requestSeq..',"obs":['..table.concat(obs,",")..'],"legal":['..table.concat(legal,",")..']}')
  req:SetHTTPRequestAbsoluteTimeoutMS(1500)
  req:Send(function(response)
    if epoch~=generation then return end
    pending=false
    if not running or Time()-sent>1.5 or not h:IsAlive() or response.StatusCode~=200 then h:Stop(); return end
    local s,a=string.match(response.Body or "", "^(%d+)|(%d+)$")
    a=tonumber(a)
    if tonumber(s)~=requestSeq or not a or a>12 or legal[a+1]~=1 then return end
    local order={UnitIndex=h:entindex(),Queue=false}
    if a>=1 and a<=8 then
      local d=directions[a]; local p=h:GetAbsOrigin()
      order.OrderType=DOTA_UNIT_ORDER_MOVE_TO_POSITION; order.Position=p+Vector(d[1]*250,d[2]*250,0)
    elseif a>=9 then
      if not target or target:IsNull() or not target:IsAlive() or not h:CanEntityBeSeenByMyTeam(target) then return end
      if a==9 then order.OrderType=DOTA_UNIT_ORDER_ATTACK_TARGET; order.TargetIndex=target:entindex()
      else
        local ability=h:FindAbilityByName(names[a-9])
        if not ability or not ability:IsFullyCastable() then return end
        order.AbilityIndex=ability:entindex()
        if a==12 then order.OrderType=DOTA_UNIT_ORDER_CAST_TARGET; order.TargetIndex=target:entindex()
        else order.OrderType=DOTA_UNIT_ORDER_CAST_POSITION; order.Position=target:GetAbsOrigin() end
      end
    else return end
    ExecuteOrderFromTable(order)
    print("FLY_ORDER",requestSeq,a,h:GetAbsOrigin().x,h:GetAbsOrigin().y)
  end)
  return .2
end
