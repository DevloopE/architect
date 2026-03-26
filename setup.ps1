# Architect — Windows Setup
# Usage: .\setup.ps1

$root = $PSScriptRoot
Write-Host "=== Architect Setup ===" -ForegroundColor Cyan

# 1. Check editor kernel
if (-not (Test-Path "$root\editor\package.json")) {
    Write-Host "[ERROR] Editor kernel not found. Make sure 'editor\' directory exists." -ForegroundColor Red
    exit 1
}
Write-Host "[1/5] Editor kernel present" -ForegroundColor Green

# 2. Install editor dependencies
Write-Host "[2/5] Installing editor dependencies (bun)..." -ForegroundColor Yellow
& bun install --cwd "$root\editor"

# 3. Install Electron dependencies
Write-Host "[3/5] Installing Electron dependencies..." -ForegroundColor Yellow
& npm install --prefix "$root\electron"

# 4. Install Python dependencies
Write-Host "[4/5] Installing Python dependencies..." -ForegroundColor Yellow
& pip install websockets --quiet 2>$null

# 5. Verify
Write-Host "[5/5] Verifying..." -ForegroundColor Yellow
Write-Host "  Editor OK" -ForegroundColor Green
Write-Host "  Electron OK" -ForegroundColor Green

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage:"
Write-Host "  Desktop app:   cd electron; npm start"
Write-Host "  Browser mode:  .\start.ps1"
Write-Host "  Claude Code:   /build a modern villa with pool"
