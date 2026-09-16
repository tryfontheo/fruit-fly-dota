param([switch]$SelfPlay,[switch]$Curriculum,[string]$DotaRoot='C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta')
$ErrorActionPreference='Stop'
& "$PSScriptRoot\install_dota.ps1" -DotaRoot $DotaRoot
# Override only this project's installed addon, never stock Dota files.
$(if($Curriculum){'return "curriculum"'}elseif($SelfPlay){'return "selfplay"'}else{'return true'}) | Set-Content (Join-Path $DotaRoot 'game\dota_addons\fruit_fly_dota\scripts\vscripts\auto_training.lua')
& "$PSScriptRoot\start_training.ps1"
if (!(Get-Process dota2 -ErrorAction SilentlyContinue)) {
  Start-Process (Join-Path $DotaRoot 'game\bin\win64\dota2.exe') -ArgumentList @('-tools','-addon','fruit_fly_dota','-novid','-windowed','-w','1280','-h','720','-console','-condebug','+dota_launch_custom_game','fruit_fly_dota','dota') -WindowStyle Hidden
} else { Write-Output 'Dota is open. Load the fruit_fly_dota local addon to start practice automatically.' }
