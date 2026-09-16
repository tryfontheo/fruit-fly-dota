-- Local-only full-map shared-policy experiment. No public matchmaking automation.
local agents={}
local session=nil
local active=false
local outcomeSent=false
local desiredMode="practice"
local roundSeconds=300
local starting={}
function Precache(context)
  PrecacheUnitByNameSync("npc_dota_hero_nevermore",context)
  PrecacheUnitByNameSync("npc_dota_creep_badguys_melee",context)
end
local function attach(id)
  if agents[id] or starting[id] then return end
  local player=PlayerResource:GetPlayer(id)
  if not player then return end
  starting[id]=true
  PrecacheUnitByNameAsync("npc_dota_hero_nevermore",function()
    if not active then starting[id]=nil;return end
    local hero=PlayerResource:GetSelectedHeroEntity(id)
    if not hero then hero=CreateHeroForPlayer("npc_dota_hero_nevermore",player)
    elseif hero:GetUnitName()~="npc_dota_hero_nevermore" then hero=PlayerResource:ReplaceHeroWith(id,"npc_dota_hero_nevermore",600,0) end
    if not hero then starting[id]=nil;return end
    hero:SetIdleAcquire(false)
    local spawn=Entities:FindByClassname(nil,hero:GetTeamNumber()==DOTA_TEAM_GOODGUYS and "info_player_start_goodguys" or "info_player_start_badguys")
    if spawn then FindClearSpaceForUnit(hero,spawn:GetAbsOrigin(),true);hero:SetRespawnPosition(spawn:GetAbsOrigin()) end
    if id==0 then hero:SetControllableByPlayer(0,true);PlayerResource:SetCameraTarget(0,hero) end
    agents[id]=require("neural_agent").new(hero,id,session)
    if desiredMode=="practice" then agents[id].practice(roundSeconds) end
    GameRules:GetGameModeEntity():SetContextThink("FlyAgent"..id,agents[id].think,.1+id*.015)
    print("FLY_AGENT_READY",id,hero:GetTeamNumber(),hero:entindex())
  end,id)
end
local function finish(winner)
  if outcomeSent then return end
  outcomeSent=true
  for _,a in pairs(agents) do a.finish(winner) end
  if desiredMode=="selfplay" then
    GameRules:GetGameModeEntity():SetContextThink("FlyNextMatch",function()
      if active then SendToServerConsole("dota_launch_custom_game fruit_fly_dota dota") end
      return nil
    end,15)
  end
end
function Activate()
  session=tostring(RandomInt(100000,999999999))
  assert(IsInToolsMode(),"Only local Workshop Tools games are supported")
  local mode=GameRules:GetGameModeEntity()
  GameRules:SetCustomGameTeamMaxPlayers(DOTA_TEAM_GOODGUYS,5);GameRules:SetCustomGameTeamMaxPlayers(DOTA_TEAM_BADGUYS,5)
  GameRules:SetSameHeroSelectionEnabled(true);mode:SetCustomGameForceHero("npc_dota_hero_nevermore")
  GameRules:SetHeroSelectionTime(0);GameRules:SetPreGameTime(0);GameRules:SetStartingGold(600);GameRules:SetCustomGameSetupTimeout(0)
  GameRules:SetGoldPerTick(0)
  local economy=require("economy");local goldTime=nil
  mode:SetContextThink("FlyPassiveGold",function()
    local now=GameRules:GetDOTATime(false,false)
    if GameRules:IsGamePaused() or now<0 then return .1 end
    local amount;goldTime,amount=economy.advance(goldTime,now)
    if amount>0 then for id=0,23 do if PlayerResource:IsValidPlayerID(id) then PlayerResource:ModifyGold(id,amount,true,DOTA_ModifyGold_GameTick) end end end
    return .1
  end,.1)
  Convars:RegisterCommand("fly_start",function() active=true;attach(0);if agents[0] then agents[0].resume() end end,"Start neural SF",0)
  Convars:RegisterCommand("fly_train",function() desiredMode="practice";active=true;attach(0);if agents[0] then agents[0].practice(roundSeconds) end end,"Five-minute practice rounds",0)
  Convars:RegisterCommand("fly_round_seconds",function(_,value) local n=tonumber(value);if n and n>=60 and n<=3600 then roundSeconds=n;if agents[0] and desiredMode=="practice" then agents[0].practice(n) end end end,"Set practice length 60..3600 seconds",0)
  Convars:RegisterCommand("fly_selfplay",function()
    desiredMode="selfplay";active=true;for _,a in pairs(agents) do a.match() end
    local player=PlayerResource:GetPlayer(0)
    if player then player:SetTeam(DOTA_TEAM_GOODGUYS);PlayerResource:SetCustomTeamAssignment(0,DOTA_TEAM_GOODGUYS) end
    attach(0)
    mode:SetBotThinkingEnabled(true)
    mode:SetContextThink("FlyPopulateAfterOwner",function()
      if not active then return nil end
      if not agents[0] then return .2 end
      SendToServerConsole("dota_bot_populate");return nil
    end,.2)
    print("FLY_SELFPLAY_REQUESTED")
    mode:SetContextThink("FlyAttachTeams",function()
      if not active then return nil end
      mode:SetBotThinkingEnabled(false)
      local count=0
      for id=0,23 do
        if PlayerResource:IsValidPlayerID(id) and PlayerResource:GetPlayer(id) then attach(id) end
        if agents[id] then count=count+1 end
      end
      if count>=10 then mode:SetBotThinkingEnabled(false);print("FLY_TEN_NEURAL_HEROES_READY");return nil end
      return 1
    end,2)
  end,"Local 5v5 shared-policy SF self-play",0)
  Convars:RegisterCommand("fly_stop",function() active=false;for _,a in pairs(agents) do a.stop() end end,"Stop all neural heroes",0)
  Convars:RegisterCommand("fly_camera_follow",function(_,value) local id=tonumber(value) or 0;if agents[id] then PlayerResource:SetCameraTarget(0,agents[id].hero) end end,"Follow a neural hero by player ID",0)
  Convars:RegisterCommand("fly_camera_free",function() PlayerResource:SetCameraTarget(0,nil) end,"Release camera",0)
  ListenToGameEvent("dota_match_done",function(e) finish(e.winningteam) end,nil)
  ListenToGameEvent("entity_killed",function(e)
    local victim=e.entindex_killed and EntIndexToHScript(e.entindex_killed)
    if victim then
      local name=victim:GetUnitName()
      if name=="npc_dota_goodguys_fort" then finish(DOTA_TEAM_BADGUYS)
      elseif name=="npc_dota_badguys_fort" then finish(DOTA_TEAM_GOODGUYS) end
    end
  end,nil)
  local ok,auto=pcall(require,"auto_training")
  if ok and auto=="curriculum" then
    local placed={}
    mode:SetContextThink("FlyLaneStartCurriculum",function()
      if not active or GameRules:GetDOTATime(false,false)<45 then return 1 end
      local remaining=0
      local creeps=Entities:FindAllByClassname("npc_dota_creep_lane")
      for id,a in pairs(agents) do
        if not placed[id] then
          local h=a.hero
          local spawn=Entities:FindByClassname(nil,h:GetTeamNumber()==DOTA_TEAM_GOODGUYS and "info_player_start_goodguys" or "info_player_start_badguys")
          local target=spawn and require("lane_start").position(h,creeps,spawn:GetAbsOrigin())
          if target and h:IsAlive() then
            h:Stop();FindClearSpaceForUnit(h,target,true);a.boundary();placed[id]=true
            print("FLY_LANE_START",id,target.x,target.y)
          else remaining=remaining+1 end
        end
      end
      local count=0;for _ in pairs(placed) do count=count+1 end
      if count>=10 and remaining==0 then return nil end
      return 1
    end,1)
  end
  if ok and auto then
    mode:SetContextThink("FlyAutoStart",function()
      if not PlayerResource:GetPlayer(0) then return 1 end
      SendToServerConsole((auto=="selfplay" or auto=="curriculum") and "fly_selfplay" or "fly_train");return nil
    end,1)
  end
  mode:SetContextThink("FlyMatchTimeout",function()
    if active and desiredMode=="selfplay" and not outcomeSent and GameRules:GetDOTATime(false,false)>=1800 then finish(0) end
    return 1
  end,1)
  print("FLY_SHARED_ADDON_READY: fly_train or fly_selfplay")
end
