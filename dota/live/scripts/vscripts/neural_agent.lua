-- Independent per-hero controller state; all decisions come from shared Python policy.
local M={}
function M.new(hero,playerID,session)
local running, pending, seq, generation = true, false, 0, 0
local previousApplied=false
local controlledHero=hero
local matchMode=false
local playerActions=require("player_actions")
local guideItems=require("guide_items")
local guideSeen={}
local rewardRules=require("reward_rules")
local rewardPending=0
local rewardComponents={}
local damageLedger=setmetatable({},{__mode="k"})
local lastPosition=nil
local idleSince=0
local decisionInterval=.1
local lastDecisionTime=nil
local training=false
local roundDeadline=0
local roundEnded=false
local practiceCreeps={}
local xpHighWater=nil
local lastRuneTimes={}
local function reward(value,reason)
  if not running then return end
  if value==0 then return end
  rewardComponents[reason]=(rewardComponents[reason] or 0)+value
  rewardPending=math.max(-200,math.min(200,rewardPending+value))
  print("FLY_REWARD",value,reason)
end
local function stop()
  training=false; running=false; generation=generation+1; pending=false
  local h=controlledHero
  if h then h:Stop() end
  local p=PlayerResource:GetPlayer(playerID)
  if p and h then CustomGameEventManager:Send_ServerToPlayer(p,"fly_status",{entity=h:entindex(),status="STOPPED",action="No current command"}) end
  print("FLY_STOP")
end
local interactions=require("interactions")
local spellFeedback=require("spell_feedback").new()
local roundSeconds=300
local terminalPending=nil
local terminalSeq=nil
xpHighWater=hero:GetCurrentXP()
ListenToGameEvent("dota_player_used_ability",function(e)
  if e.caster_entindex~=hero:entindex() then return end
  local name=e.abilityname or ""
  spellFeedback.cast(name,Time())
end,nil)
local function sendTerminal()
  if pending then return end
  terminalSeq=terminalSeq or seq
  local obs,legal={},{}
  for i=1,78 do obs[i]=0 end
  for i=1,54 do legal[i]=i==1 and 1 or 0 end
  local req=CreateHTTPRequestScriptVM("POST","http://127.0.0.1:8765/step")
  req:SetHTTPRequestRawPostBody("application/json",'{"env":"local","agent":"'..playerID..'","session":"'..session..'","seq":'..terminalSeq..',"terminal":true,"reward":'..terminalPending..',"dt":1,"obs":['..table.concat(obs,",")..'],"legal":['..table.concat(legal,",")..']}')
  req:SetHTTPRequestAbsoluteTimeoutMS(3000);pending=true
  req:Send(function(response)
    pending=false
    if response.StatusCode==200 then running=false;terminalPending=nil;hero:Stop();print("FLY_TERMINAL_SAVED",playerID) end
  end)
end
  ListenToGameEvent("dota_rune_activated_server",function(e)
    if not controlledHero or e.PlayerID~=controlledHero:GetPlayerOwnerID() then return end
    local key=tostring(e.rune)
    local now=Time()
    if not lastRuneTimes[key] or now-lastRuneTimes[key]>1 then
      lastRuneTimes[key]=now;reward(.2,"rune_activation")
    end
  end,nil)
  ListenToGameEvent("entity_killed",function(e)
    if not controlledHero then return end
    local victim=e.entindex_killed and EntIndexToHScript(e.entindex_killed)
    local attacker=e.entindex_attacker and EntIndexToHScript(e.entindex_attacker)
    if victim==controlledHero then reward(rewardRules.death,"death")
    elseif attacker==controlledHero and victim and victim:GetTeamNumber()~=controlledHero:GetTeamNumber() then
      if victim:IsRealHero() then reward(rewardRules.hero_kill,"hero_kill")
      elseif victim:IsBuilding() then reward(rewardRules.building_kill,"building_kill")
      elseif victim:IsCreep() then reward(rewardRules.last_hit,victim:GetTeamNumber()==DOTA_TEAM_NEUTRALS and "jungle_last_hit" or "last_hit") end
    elseif attacker==controlledHero and victim and victim:IsCreep() and victim:GetTeamNumber()==controlledHero:GetTeamNumber() then
      reward(rewardRules.deny,"deny")
    end
  end,nil)
  ListenToGameEvent("entity_hurt",function(e)
    if not controlledHero or not e.entindex_attacker or not e.entindex_killed then return end
    local attacker=EntIndexToHScript(e.entindex_attacker)
    local victim=EntIndexToHScript(e.entindex_killed)
    if victim==controlledHero and attacker and attacker:GetTeamNumber()~=controlledHero:GetTeamNumber() then
      local tower=attacker:IsTower()
      reward(rewardRules.damage_taken(e.damage,controlledHero:GetMaxHealth(),tower),tower and "tower_damage_taken" or "damage_taken")
    end
    local spellName=nil
    if attacker==controlledHero and victim and victim:GetTeamNumber()~=controlledHero:GetTeamNumber() and e.entindex_inflictor then
      local inflictor=EntIndexToHScript(e.entindex_inflictor)
      if inflictor and (tonumber(e.damage) or 0)>0 then
        spellName=inflictor:GetAbilityName();spellFeedback.damage(spellName,Time())
      end
    end
    if attacker==controlledHero and victim and victim:GetTeamNumber()~=controlledHero:GetTeamNumber() then
      local kind=victim:IsBuilding() and "building" or (victim:IsRealHero() and "hero" or (victim:IsCreep() and "creep" or nil))
      if kind then
        local reason=victim:GetTeamNumber()==DOTA_TEAM_NEUTRALS and "jungle_damage" or kind.."_damage"
        if spellName and string.find(spellName,"nevermore_shadowraze",1,true)==1 then reason="raze_damage"
        elseif spellName=="nevermore_requiem" then reason="ultimate_damage" end
        reward(rewardRules.damage_dealt(damageLedger,victim,e.damage,victim:GetMaxHealth(),kind),reason)
      end
    end
  end,nil)
local directions={{1,0},{.707,.707},{0,1},{-.707,.707},{-1,0},{-.707,-.707},{0,-1},{.707,-.707}}
local function think()
  if not running or not IsInToolsMode() or GameRules:IsGamePaused() then return .2 end
  if terminalPending then sendTerminal();return .2 end
  for _,cast in ipairs(spellFeedback.settle(Time())) do
    reward(cast.penalty,"missed_spell")
    print("FLY_SPELL_RESULT",playerID,cast.name,cast.hit and "hit" or "miss")
  end
  local h=controlledHero
  if not h then return .2 end
  for slot=0,8 do
    local item=h:GetItemInSlot(slot)
    if item then reward(guideItems.claim(guideSeen,item:GetAbilityName()),"guide_item") end
  end
  local xpReward
  xpHighWater,xpReward=rewardRules.experience(xpHighWater,h:GetCurrentXP())
  reward(xpReward,"experience")
  if training and not pending and (Time()>=roundDeadline or not h:IsAlive()) then
    roundEnded=roundDeadline>0
    for _,creep in ipairs(practiceCreeps) do
      if not creep:IsNull() then UTIL_Remove(creep) end
    end
    practiceCreeps={}
    if not h:IsAlive() then h:RespawnHero(false,false) end
    h:Stop()
    local origin=Vector(-1800,-1400,256)
    FindClearSpaceForUnit(h,origin,true)
    h:SetHealth(h:GetMaxHealth());h:SetMana(h:GetMaxMana())
    for i=1,3 do
      local creep=CreateUnitByName("npc_dota_creep_badguys_melee",origin+Vector(450,i*100-200,0),true,nil,nil,DOTA_TEAM_BADGUYS)
      if creep then table.insert(practiceCreeps,creep) end
    end
    roundDeadline=Time()+roundSeconds
    lastPosition=nil;idleSince=Time()
    if playerID==0 then PlayerResource:SetCameraTarget(0,h) end
    print("FLY_TRAIN_ROUND",seq)
  end
  if not h:IsAlive() then return .2 end
  if pending then return decisionInterval end
  -- Do not overwrite channeling or a spell's cast point with a new move.
  if h:IsChanneling() then return .2 end
  for i=0,19 do
    local ability=h:GetAbilityByIndex(i)
    if ability and ability:IsInAbilityPhase() then return .2 end
  end
  local pos=h:GetAbsOrigin()
  local units=FindUnitsInRadius(h:GetTeamNumber(),pos,nil,1600,DOTA_UNIT_TARGET_TEAM_ENEMY,
    DOTA_UNIT_TARGET_HERO+DOTA_UNIT_TARGET_BASIC+DOTA_UNIT_TARGET_BUILDING,
    DOTA_UNIT_TARGET_FLAG_FOW_VISIBLE+DOTA_UNIT_TARGET_FLAG_NO_INVIS,FIND_CLOSEST,false)
  local target=units[1]
  if target and not h:CanEntityBeSeenByMyTeam(target) then target=nil end
  local delta=target and (target:GetAbsOrigin()-pos) or Vector(0,0,0)
  -- No movement/idle reward: waiting and holding position may be correct.
  local obs={pos.x/8192,pos.y/8192,h:GetHealth()/h:GetMaxHealth(),h:GetMana()/math.max(1,h:GetMaxMana()),
    h:GetLevel()/30,h:GetGold()/30000,h:Script_GetAttackRange()/2000,GameRules:GetDOTATime(false,false)/7200,
    delta.x/1600,delta.y/1600,target and target:GetHealth()/math.max(1,target:GetMaxHealth()) or 0,
    target and 1 or 0,target and target:IsHero() and 1 or 0,0,0,0,0}
  local legal={1,1,1,1,1,1,1,1,1,target and 1 or 0,0,0,0,0}
  -- Observable tower context, never a suggested action or retreat command.
  local tower=nil
  for _,u in ipairs(units) do if u:IsTower() and h:CanEntityBeSeenByMyTeam(u) then tower=u;break end end
  local td=tower and tower:GetAbsOrigin()-pos or Vector(0,0,0)
  table.insert(obs,td.x/1600);table.insert(obs,td.y/1600)
  table.insert(obs,tower and tower:Script_GetAttackRange()/1600 or 0)
  table.insert(obs,tower and 1 or 0)
  table.insert(obs,h:GetAbilityPoints()/30)
  local names={"nevermore_shadowraze1","nevermore_shadowraze2","nevermore_shadowraze3","nevermore_requiem"}
  for i,name in ipairs(names) do
    local a=h:FindAbilityByName(name)
    local ready=a and a:GetLevel()>0 and a:IsFullyCastable() and not h:IsSilenced()
    obs[13+i]=ready and 1 or 0
    -- Raze/Requiem are no-target casts. No automatic aiming or tactical range mask.
    legal[10+i]=ready and 1 or 0
  end
  playerActions.append_legal(h,legal)
  playerActions.append_observation(h,obs)
  local frenzy=h:FindAbilityByName("nevermore_frenzy")
  legal[26]=(frenzy and frenzy:GetLevel()>0 and frenzy:IsFullyCastable() and not h:IsSilenced()) and 1 or 0
  guideItems.observe(h,obs,legal,playerActions)
  local clickContext=interactions.context(h,units,obs,legal)
  require("wave_observation").append(h,obs)
  local requestSeq=seq; seq=seq+1
  local dt=lastDecisionTime and math.min(60,math.max(.001,Time()-lastDecisionTime)) or decisionInterval
  lastDecisionTime=Time()
  local epoch=generation; local sent=Time(); pending=true
  local req=CreateHTTPRequestScriptVM("POST","http://127.0.0.1:8765/step")
  local deliveredReward=rewardPending;rewardPending=0
  local componentParts={}
  for reason,value in pairs(rewardComponents) do table.insert(componentParts,'"'..reason..'":'..value) end
  rewardComponents={}
  local componentJSON="{"..table.concat(componentParts,",").."}"
  local deliveredRound=roundEnded;roundEnded=false
  req:SetHTTPRequestRawPostBody("application/json",'{"env":"local","agent":"'..playerID..'","session":"'..session..'","seq":'..requestSeq..',"previous_applied":'..tostring(previousApplied)..',"dt":'..dt..',"round_end":'..tostring(deliveredRound)..',"reward_version":"'..rewardRules.version..'","reward_components":'..componentJSON..',"assisted":false,"reward":'..deliveredReward..',"obs":['..table.concat(obs,",")..'],"legal":['..table.concat(legal,",")..']}')
  previousApplied=false
  req:SetHTTPRequestAbsoluteTimeoutMS(1500)
  req:Send(function(response)
    if epoch~=generation then return end
    pending=false
    if not running or Time()-sent>1.5 or not h:IsAlive() or response.StatusCode~=200 then h:Stop(); return end
    local s,a=string.match(response.Body or "", "^(%d+)|(%d+)$")
    a=tonumber(a)
    if tonumber(s)~=requestSeq or not a or a>53 or legal[a+1]~=1 then return end
    if a>=39 then previousApplied=interactions.apply(h,a,clickContext);return end
    if a>=26 then previousApplied=guideItems.apply(h,a,playerActions);return end
    if a>=14 and a<=24 then previousApplied=playerActions.apply(h,a);return end
    local order={UnitIndex=h:entindex(),Queue=false}
    if a>=1 and a<=8 then
      local d=directions[a]; local p=h:GetAbsOrigin()
      order.OrderType=DOTA_UNIT_ORDER_MOVE_TO_POSITION; order.Position=p+Vector(d[1]*250,d[2]*250,0)
    elseif a==9 then
      if not target or target:IsNull() or not target:IsAlive() or not h:CanEntityBeSeenByMyTeam(target) then return end
      order.OrderType=DOTA_UNIT_ORDER_ATTACK_TARGET; order.TargetIndex=target:entindex()
    elseif a>=10 then
        local ability=h:FindAbilityByName(a==25 and "nevermore_frenzy" or names[a-9])
        if not ability or not ability:IsFullyCastable() then return end
        order.AbilityIndex=ability:entindex()
        order.OrderType=DOTA_UNIT_ORDER_CAST_NO_TARGET
    else
      previousApplied=true
      CustomGameEventManager:Send_ServerToPlayer(PlayerResource:GetPlayer(playerID),"fly_status",{entity=h:entindex(),status="Full connectome â€” policy status in dashboard",action="Wait / continue previous order",seq=requestSeq})
      return
    end
    ExecuteOrderFromTable(order)
    previousApplied=true
    local labels={[1]="Move east",[2]="Move northeast",[3]="Move north",[4]="Move northwest",[5]="Move west",[6]="Move southwest",[7]="Move south",[8]="Move southeast",[9]="Attack",[10]="Near raze",[11]="Medium raze",[12]="Far raze",[13]="Requiem",[25]="Frenzy (R)"}
    CustomGameEventManager:Send_ServerToPlayer(PlayerResource:GetPlayer(playerID),"fly_status",{entity=h:entindex(),status="Full connectome â€” policy status in dashboard",action=labels[a],seq=requestSeq})
    print("FLY_ORDER",requestSeq,a,h:GetAbsOrigin().x,h:GetAbsOrigin().y)
  end)
  return decisionInterval
end

return {hero=hero,think=think,stop=stop,
  match=function() training=false;running=true end,
  resume=function() running=true end,
  practice=function(seconds) running=true;training=true;roundSeconds=seconds or 300;roundDeadline=0 end,
  finish=function(winner)
    if terminalPending then return end
    terminalPending=rewardPending+(winner==hero:GetTeamNumber() and 100 or (winner==0 and 0 or -100))
    training=false;print("FLY_MATCH_OUTCOME",playerID,winner,terminalPending)
  end}
end
return M
