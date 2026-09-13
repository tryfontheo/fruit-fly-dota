-- Local real-map experiment. Policy provenance is reported by the Python server.
-- All observations, target selection and compass actions are engineered.
local running, pending, seq, generation = false, false, 0, 0
local controlledHero=nil
local matchMode=false
local function stop()
  running=false; generation=generation+1; pending=false
  local h=controlledHero
  if h then h:Stop() end
  local p=PlayerResource:GetPlayer(0)
  if p and h then CustomGameEventManager:Send_ServerToPlayer(p,"fly_status",{entity=h:entindex(),status="STOPPED",action="No current command"}) end
  print("FLY_STOP")
end
function Precache(context) PrecacheUnitByNameSync("npc_dota_hero_nevermore", context) end
function Activate()
  assert(IsInToolsMode(), "Only local Workshop Tools games are supported")
  local mode=GameRules:GetGameModeEntity()
  GameRules:SetCustomGameTeamMaxPlayers(DOTA_TEAM_GOODGUYS,5)
  GameRules:SetCustomGameTeamMaxPlayers(DOTA_TEAM_BADGUYS,5)
  mode:SetBotThinkingEnabled(true)
  mode:SetCustomGameForceHero("npc_dota_hero_nevermore")
  GameRules:SetHeroSelectionTime(0)
  GameRules:SetPreGameTime(0)
  GameRules:SetStartingGold(600)
  GameRules:SetCustomGameSetupTimeout(0)
  Convars:RegisterCommand("fly_start", function()
    stop()
    local player=PlayerResource:GetPlayer(0)
    if not player then print("FLY_NO_LOCAL_PLAYER"); return end
    if not controlledHero then
      player:SetTeam(DOTA_TEAM_GOODGUYS)
      PlayerResource:SetCustomTeamAssignment(0,DOTA_TEAM_GOODGUYS)
      -- Include player-specific resources before spawning a controllable hero.
      local setupEpoch=generation
      PrecacheUnitByNameAsync("npc_dota_hero_nevermore",function()
        if setupEpoch~=generation then return end
        controlledHero=CreateHeroForPlayer("npc_dota_hero_nevermore",player)
        -- Late-created custom-game heroes otherwise appear at map origin.
        local spawn=Entities:FindByClassname(nil,"info_player_start_goodguys")
        if not spawn then
          print("FLY_SPAWN_MISSING: controller stopped; inspect map spawn entities")
          stop();return
        end
        local origin=spawn:GetAbsOrigin()
        FindClearSpaceForUnit(controlledHero,origin,true)
        controlledHero:SetRespawnPosition(origin)
        controlledHero:SetControllableByPlayer(0,true)
        PlayerResource:SetCameraTarget(0,controlledHero)
        CustomGameEventManager:Send_ServerToPlayer(player,"fly_status",{entity=controlledHero:entindex(),status="Shadow Fiend â€” connectome controller",action="Waiting for neural decision"})
        print("FLY_HERO_READY")
      end,0)
    end
    seq=0; running=true; print("FLY_START_CONTROLLER")
  end, "Enable full-connectome controller", 0)
  Convars:RegisterCommand("fly_stop", stop, "Stop controller and hero", 0)
  Convars:RegisterCommand("fly_camera_follow",function() if controlledHero then PlayerResource:SetCameraTarget(0,controlledHero) end end,"Follow fly hero",0)
  Convars:RegisterCommand("fly_camera_free",function() PlayerResource:SetCameraTarget(0,nil) end,"Release camera",0)
  Convars:RegisterCommand("fly_match",function()
    if not controlledHero then print("Use fly_start before fly_match");return end
    matchMode=true
    SendToServerConsole("dota_bot_populate")
    print("FLY_BOT_MATCH_REQUESTED: normal map, default bots, no item automation")
  end,"Fill remaining local slots with bots",0)
  mode:SetContextThink("FlyThink", FlyThink, .2)
  print("FLY_ADDON_READY: use fly_start; fly_stop disables control")
end
local directions={{1,0},{.707,.707},{0,1},{-.707,.707},{-1,0},{-.707,-.707},{0,-1},{.707,-.707}}
function FlyThink()
  if not running or not IsInToolsMode() or GameRules:IsGamePaused() then return .2 end
  local h=controlledHero
  if not h or not h:IsAlive() or pending then return .2 end
  -- Do not overwrite channeling or a spell's cast point with a new move.
  if h:IsChanneling() then return .2 end
  for i=0,19 do
    local ability=h:GetAbilityByIndex(i)
    if ability and ability:IsInAbilityPhase() then return .2 end
  end
  -- Explicit engineered skill priority for the initial match evaluation.
  if matchMode and h:GetAbilityPoints()>0 then
    for _,name in ipairs({"nevermore_requiem","nevermore_shadowraze1","nevermore_necromastery","nevermore_dark_lord","nevermore_frenzy"}) do
      local ability=h:FindAbilityByName(name)
      if ability and ability:CanAbilityBeUpgraded()==ABILITY_CAN_BE_UPGRADED then h:UpgradeAbility(ability);break end
    end
  end
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
    target and 1 or 0,target and target:IsHero() and 1 or 0,0,0,0,0}
  local legal={1,1,1,1,1,1,1,1,1,target and 1 or 0,0,0,0,0}
  local names={"nevermore_shadowraze1","nevermore_shadowraze2","nevermore_shadowraze3","nevermore_requiem"}
  for i,name in ipairs(names) do
    local a=h:FindAbilityByName(name)
    local ready=a and a:GetLevel()>0 and a:IsFullyCastable() and not h:IsSilenced()
    obs[13+i]=ready and 1 or 0
    -- Raze/Requiem are no-target casts. No automatic aiming or tactical range mask.
    legal[10+i]=ready and 1 or 0
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
    if tonumber(s)~=requestSeq or not a or a>13 or legal[a+1]~=1 then return end
    local order={UnitIndex=h:entindex(),Queue=false}
    if a>=1 and a<=8 then
      local d=directions[a]; local p=h:GetAbsOrigin()
      order.OrderType=DOTA_UNIT_ORDER_MOVE_TO_POSITION; order.Position=p+Vector(d[1]*250,d[2]*250,0)
    elseif a==9 then
      if not target or target:IsNull() or not target:IsAlive() or not h:CanEntityBeSeenByMyTeam(target) then return end
      order.OrderType=DOTA_UNIT_ORDER_ATTACK_TARGET; order.TargetIndex=target:entindex()
    elseif a>=10 then
        local ability=h:FindAbilityByName(names[a-9])
        if not ability or not ability:IsFullyCastable() then return end
        order.AbilityIndex=ability:entindex()
        order.OrderType=DOTA_UNIT_ORDER_CAST_NO_TARGET
    else
      CustomGameEventManager:Send_ServerToPlayer(PlayerResource:GetPlayer(0),"fly_status",{entity=h:entindex(),status="Full connectome â€” policy status in dashboard",action="Wait / continue previous order",seq=requestSeq})
      return
    end
    ExecuteOrderFromTable(order)
    local labels={[1]="Move east",[2]="Move northeast",[3]="Move north",[4]="Move northwest",[5]="Move west",[6]="Move southwest",[7]="Move south",[8]="Move southeast",[9]="Attack",[10]="Near raze",[11]="Medium raze",[12]="Far raze",[13]="Requiem"}
    CustomGameEventManager:Send_ServerToPlayer(PlayerResource:GetPlayer(0),"fly_status",{entity=h:entindex(),status="Full connectome â€” policy status in dashboard",action=labels[a],seq=requestSeq})
    print("FLY_ORDER",requestSeq,a,h:GetAbsOrigin().x,h:GetAbsOrigin().y)
  end)
  return 1.0 -- Match the replay label window; give attacks time to launch.
end
