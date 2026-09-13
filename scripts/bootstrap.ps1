$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path .venv)) { python -m venv .venv }
& .venv\Scripts\python.exe -m pip install -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& .venv\Scripts\python.exe -m pip install --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw 'Project installation failed' }
& .venv\Scripts\python.exe -m fruit_fly_dota.cli prepare
if ($LASTEXITCODE -ne 0) { throw 'Data preparation failed' }
& .venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
