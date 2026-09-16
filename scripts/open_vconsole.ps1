param([string]$DotaRoot='C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta')
$ErrorActionPreference='Stop'
$console=Join-Path $DotaRoot 'game\bin\win64\vconsole2.exe'
if (!(Test-Path -LiteralPath $console)) { throw "VConsole2 was not found at $console. Install Dota 2 Workshop Tools in Steam." }
Start-Process -FilePath $console -WindowStyle Normal
Write-Output 'VConsole2 opened. Start a fly mode from the menu to connect it to the local game.'
