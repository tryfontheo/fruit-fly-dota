param([switch]$Worker)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $repoRoot
$python=Join-Path $repoRoot '.venv\Scripts\python.exe'
$work=Join-Path $repoRoot 'work'
New-Item -ItemType Directory -Force $work | Out-Null
if (!$Worker) {
  try { $null=Invoke-WebRequest 'http://127.0.0.1:8765/state' -UseBasicParsing -TimeoutSec 2; Write-Output 'Controller already running. Open http://127.0.0.1:8765/'; exit } catch {}
  $p=Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"'),'-Worker') -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
  $p.Id | Set-Content (Join-Path $work 'trainer-supervisor.pid')
  Write-Output 'Local trainer started. It saves automatically and restarts after a worker failure. Dashboard: http://127.0.0.1:8765/'
  exit
}
# This supervisor belongs to this project; no Codex service or account is needed.
while (!(Test-Path (Join-Path $work 'stop-training'))) {
  $arguments=@('-m','fruit_fly_dota.live','--learn','--log','work/autonomous-v3.jsonl')
  if(Test-Path 'work/autonomous-v3.learning.npz'){$arguments+=@('--resume-learning','work/autonomous-v3.learning.npz')}
  $ErrorActionPreference='Continue'
  & $python @arguments >> (Join-Path $work 'trainer.log') 2>&1
  $workerExit=$LASTEXITCODE
  $ErrorActionPreference='Stop'
  if($workerExit -eq 0){break}
  Start-Sleep -Seconds 5
}
