param([string]$DotaRoot='C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta')
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'install_dota.ps1') -DotaRoot $DotaRoot
if (Get-Process dota2 -ErrorAction SilentlyContinue) { throw 'Dota is already running. Use its Workshop console to load the addon, or close Dota first.' }
Start-Process -FilePath (Join-Path $DotaRoot 'game\bin\win64\dota2.exe') -ArgumentList '-tools','-addon','fruit_fly_dota','-novid','-windowed','-w','1280','-h','720','-console','-condebug','+dota_launch_custom_game','fruit_fly_dota','dota' -WindowStyle Hidden
