@echo off
setlocal
cd /d "%~dp0"
title Fruit Fly Dota
:menu
cls
echo FRUIT FLY DOTA
echo.
echo 1. Start 5 vs 5 training - continue saved learning
echo 2. Start lane practice - continue saved learning
echo 3. Open brain and action dashboard
echo 4. Check training and last save
echo 5. Start faster practice - 5v5 with idle curriculum resets
echo Q. Close this menu - training keeps running
echo.
echo Before starting a new game, close Dota if it is already open.
echo Keep Steam signed in and your computer awake.
echo Learning saves automatically. Closing this menu does not stop it.
echo To stop playing, close Dota. Start again here next time.
echo.
choice /c 12345Q /n /m "Choose 1, 2, 3, 4, 5 or Q: "
if errorlevel 6 exit /b
if errorlevel 5 goto fast
if errorlevel 4 goto status
if errorlevel 3 goto dashboard
if errorlevel 2 goto practice
if errorlevel 1 goto selfplay
:selfplay
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_practice.ps1" -SelfPlay
echo.
echo Choose option 3 to watch the brain once the game starts.
pause
goto menu
:fast
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_practice.ps1" -Curriculum
pause
goto menu
:practice
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_practice.ps1"
pause
goto menu
:dashboard
start "" "http://127.0.0.1:8765/"
goto menu
:status
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\training_status.py"
pause
goto menu
