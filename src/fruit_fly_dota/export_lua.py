"""Export frozen inference to a tools-only addon: no network/keyboard bridge."""
import argparse
import json
from pathlib import Path
import numpy as np
from .connectome import load
from .neural import Reservoir

def table(a):
    if isinstance(a, (list, np.ndarray)):
        return "{" + ",".join(table(v) for v in a) + "}"
    return format(float(a), ".17g")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="results/seed0")
    parser.add_argument("--data", default="data")
    parser.add_argument("--output", default="dota/addon/scripts/vscripts/fly_policy.lua")
    args = parser.parse_args()
    config = json.loads((Path(args.policy)/"policy_config.json").read_text())
    w,m = load(args.data)
    if m["weights_sha256"] != config["connectome_sha256"]:
        raise ValueError("Policy/connectome mismatch")
    b = Reservoir(w,config["seed"],config["ablation"],config["memory"])
    p = np.load(Path(args.policy)/"policy.npz",allow_pickle=False)
    coo = b.w.tocoo()
    edges = [[int(i)+1,int(j)+1,float(v)] for i,j,v in zip(coo.row,coo.col,coo.data)]
    text = '-- Generated connectivity-derived rate policy; see manifest and methodology.\nlocal M = {}\n'
    text += f'local n={b.n}\nlocal memory="{b.memory}"\n'
    for key,value in [("edges",edges),("encoder",b.encoder),("bias",b.bias),("weights",p["weights"]),("scale",p["scale"])]:
        text += f'local {key}={table(value)}\n'
    text += '''local state, previous = {}, {}
function M.reset()
  for i=1,n do state[i]=0 end
  for i=1,6 do previous[i]=0 end
end
local function tanh(x)
  local e=math.exp(-2*math.abs(x))
  return (x>=0 and 1 or -1)*(1-e)/(1+e)
end
function M.action(x)
  local input={}
  for i=1,6 do input[i]=x[i] end
  if memory=="engineered" then for i=1,6 do input[i+6]=previous[i] end end
  for i=1,6 do previous[i]=x[i] end
  if memory=="reset" then for i=1,n do state[i]=0 end end
  local drive={}
  for i=1,n do
    drive[i]=bias[i]
    for j=1,#input do drive[i]=drive[i]+encoder[i][j]*input[j] end
  end
  for step=1,4 do
    local current={}
    for i=1,n do current[i]=drive[i] end
    for _,edge in ipairs(edges) do current[edge[1]]=current[edge[1]]+edge[3]*state[edge[2]] end
    for i=1,n do state[i]=.25*state[i]+.75*tanh(current[i]) end
  end
  local best,score=0,-math.huge
  for a=1,4 do
    local value=weights[n/2+1][a]
    for i=1,n/2 do value=value+state[n/2+i]/scale[i]*weights[i][a] end
    if value>score then best,score=a-1,value end
  end
  return best
end
M.reset()
return M
'''
    path=Path(args.output); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8")
    print(path)

if __name__ == "__main__": main()
