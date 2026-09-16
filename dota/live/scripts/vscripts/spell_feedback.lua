-- Cast outcome bookkeeping. Damage may arrive just before the cast event.
local M={}
function M.new()
  local pending,recent={},{}
  local function tracked(name)
    return name=="nevermore_requiem" or string.find(name,"nevermore_shadowraze",1,true)==1
  end
  return {
    cast=function(name,now)
      if not tracked(name) then return end
      -- Duplicate event delivery must not restart the same cast's window.
      if pending[name] then return end
      pending[name]={deadline=now+(name=="nevermore_requiem" and 4 or .8),
        hit=recent[name]~=nil and now-recent[name]>=0 and now-recent[name]<=.15}
    end,
    damage=function(name,now)
      if not tracked(name) then return end
      recent[name]=now
      if pending[name] and now<=pending[name].deadline then pending[name].hit=true end
    end,
    settle=function(now)
      local results={}
      for name,cast in pairs(pending) do
        if now>=cast.deadline then
          table.insert(results,{name=name,hit=cast.hit,penalty=cast.hit and 0 or (name=="nevermore_requiem" and -.2 or -.05)})
          pending[name]=nil
        end
      end
      return results
    end}
end
return M
