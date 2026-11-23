# ============================================================================
# Windows Production Build Script — CCTV Network Discovery & Recovery Assistant
# ============================================================================
$ErrorActionPreference = "Stop"

Write-Host "=== Building CCTV Network Discovery & Recovery Assistant (Windows) ===" -ForegroundColor Cyan

Push-Location frontend
Write-Host "Running TypeScript check and Vite production build..." -ForegroundColor Yellow
npm run build
Pop-Location

Write-Host "=== Running Backend Test Suite ===" -ForegroundColor Cyan
if (Test-Path ".\.venv\Scripts\pytest.exe") {
    & ".\.venv\Scripts\pytest.exe" -q
} else {
    pytest -q
}

Write-Host "[OK] Production build and verification succeeded! Static assets output to frontend/dist" -ForegroundColor Green

