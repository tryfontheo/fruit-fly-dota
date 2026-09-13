param([string]$DotaRoot='C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta')
$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
$addonPath=Join-Path $DotaRoot 'game\dota_addons\fruit_fly_dota'
if (!(Test-Path (Join-Path $DotaRoot 'game\bin\win64\dota2.exe'))) { throw 'Install Dota 2 Workshop Tools through Steam first.' }
New-Item -ItemType Directory -Force -Path $addonPath | Out-Null
Copy-Item -Path (Join-Path $repoRoot 'dota\live\*') -Destination $addonPath -Recurse -Force
Write-Output "Installed isolated addon: $addonPath"
