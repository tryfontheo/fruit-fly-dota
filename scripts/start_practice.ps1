param([switch]$SelfPlay,[switch]$Curriculum,[string]$DotaRoot='C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta')
$ErrorActionPreference='Stop'
$dotaExe=Join-Path $DotaRoot 'game\bin\win64\dota2.exe'
if (!(Test-Path -LiteralPath $dotaExe)) { throw "Dota was not found at $dotaExe" }
$running=@(Get-CimInstance Win32_Process -Filter "Name='dota2.exe'")
foreach ($game in $running) {
  if ($game.ExecutablePath -ne $dotaExe -or $game.CommandLine -notmatch '-addon\s+"?fruit_fly_dota(?:"|\s|$)' -or $game.CommandLine -notmatch '-tools(?:\s|$)') {
    Write-Output 'A different Dota game is open. Close that game, then choose this menu option again.'
    exit 1
  }
}
& "$PSScriptRoot\install_dota.ps1" -DotaRoot $DotaRoot
# Override only this project's installed addon, never stock Dota files.
$(if($Curriculum){'return "curriculum"'}elseif($SelfPlay){'return "selfplay"'}else{'return true'}) | Set-Content (Join-Path $DotaRoot 'game\dota_addons\fruit_fly_dota\scripts\vscripts\auto_training.lua')
& "$PSScriptRoot\start_training.ps1"
foreach ($game in $running) {
  Write-Output 'Switching the local fly match. The shared trainer and saved learning stay running.'
  Stop-Process -Id $game.ProcessId -ErrorAction Stop
  Wait-Process -Id $game.ProcessId -Timeout 20 -ErrorAction SilentlyContinue
}
Start-Process $dotaExe -ArgumentList @('-tools','-addon','fruit_fly_dota','-novid','-windowed','-w','1280','-h','720','-console','-condebug','+dota_launch_custom_game','fruit_fly_dota','dota') -WindowStyle Hidden
Write-Output 'Starting your selected mode automatically. Allow about a minute for the map to load.'
