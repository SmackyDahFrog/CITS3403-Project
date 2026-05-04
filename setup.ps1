# one-shot setup for Windows PowerShell
$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "python not found - install Python 3.10+ from python.org" -ForegroundColor Red
    exit 1
}

#create venv on first run only
if (-not (Test-Path venv)) {
    python -m venv venv
}

#  install pinned dependencies from requirements.txt
& .\venv\Scripts\pip.exe install -q --upgrade pip
& .\venv\Scripts\pip.exe install -q -r requirements.txt

#apply schema migration to build app/user.db
$env:FLASK_APP = "run.py"
& .\venv\Scripts\flask.exe db upgrade

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host ""
Write-Host "Activate the venv:   .\venv\Scripts\Activate.ps1"
Write-Host "Start the server:    python run.py"
Write-Host "Run the tests:       python -m unittest tests.test_auth"
Write-Host "Reset the database:  Remove-Item app\user.db; flask db upgrade"
