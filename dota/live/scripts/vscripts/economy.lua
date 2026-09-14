-- Deterministic practice economy; no policy input or reward shaping.
local M={tick_seconds=.6}
function M.advance(previous,now)
  if previous==nil or now<previous then return now,0 end
  local ticks=math.floor((now-previous+1e-8)/M.tick_seconds)
  return previous+ticks*M.tick_seconds,ticks
end
return M
