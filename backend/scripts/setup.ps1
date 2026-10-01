$ErrorActionPreference = "Stop"
$Backend = Split-Path -Parent $PSScriptRoot
Set-Location $Backend
if (-not (Test-Path ".venv")) { python -m venv .venv }
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
Write-Host "Setup complete. Fill backend/.env privately, then run scripts/run.ps1"

