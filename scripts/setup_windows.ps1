# ============================================================================
# Windows Setup Script — CCTV Network Discovery & Recovery Assistant
# Run from PowerShell in the project root: .\scripts\setup_windows.ps1
# ============================================================================
$ErrorActionPreference = "Stop"

Write-Host "=== Setting up CCTV Network Discovery & Recovery Assistant (Windows) ===" -ForegroundColor Cyan

# 1. Create required data directories
New-Item -ItemType Directory -Force -Path "data\database", "data\logs", "data\exports", "data\backups" | Out-Null

# 2. Copy .env.example to .env if not present
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env from .env.example" -ForegroundColor Green
}

# 3. Create Python virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
}

# 4. Install Python dependencies
Write-Host "Installing Python backend and test dependencies..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements-dev.txt

# 5. Install Frontend dependencies
Write-Host "Installing React frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host "To start the backend:  .\.venv\Scripts\python.exe scripts\start_backend.py"
Write-Host "To start the frontend: cd frontend; npm run dev"
Write-Host "Note: For low-level ARP/ICMP packet capture on Windows, install Npcap (https://npcap.com) and run PowerShell as Administrator."

