param([string]$DotaRoot='C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta')
$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
$addonPath=Join-Path $DotaRoot 'game\dota_addons\fruit_fly_dota'
if (!(Test-Path (Join-Path $DotaRoot 'game\bin\win64\dota2.exe'))) { throw 'Install Dota 2 Workshop Tools through Steam first.' }
New-Item -ItemType Directory -Force -Path $addonPath | Out-Null
Copy-Item -Path (Join-Path $repoRoot 'dota\live\*') -Destination $addonPath -Recurse -Force
$contentPath=Join-Path $DotaRoot 'content\dota_addons\fruit_fly_dota'
New-Item -ItemType Directory -Force -Path $contentPath | Out-Null
Copy-Item -Path (Join-Path $repoRoot 'dota\live\panorama') -Destination $contentPath -Recurse -Force
& (Join-Path $DotaRoot 'game\bin\win64\resourcecompiler.exe') -i (Join-Path $contentPath 'panorama\layout\custom_game\custom_ui_manifest.xml') -nop4
if($LASTEXITCODE -ne 0){throw 'Panorama compilation failed'}
Write-Output "Installed isolated addon: $addonPath"
