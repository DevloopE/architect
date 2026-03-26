# Architect — Windows Start
# Usage: .\start.ps1

Write-Host "=== Starting Architect ===" -ForegroundColor Cyan

# Kill existing processes on ports 3002 and 3100
foreach ($port in 3002, 3100) {
    $pids = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING" |
        ForEach-Object { ($_ -split '\s+')[-1] } | Sort-Object -Unique
    foreach ($pid in $pids) {
        if ($pid -and $pid -ne "0") {
            try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}
Start-Sleep -Seconds 1

# Start relay
Write-Host "Starting WebSocket relay on ws://localhost:3100..." -ForegroundColor Yellow
$relayDir = Join-Path $PSScriptRoot "editor\apps\editor"
Start-Process -NoNewWindow -FilePath "node" -ArgumentList "bridge-relay.mjs" -WorkingDirectory $relayDir

# Start editor
Write-Host "Starting editor on http://localhost:3002..." -ForegroundColor Yellow
$editorDir = Join-Path $PSScriptRoot "editor"
Start-Process -NoNewWindow -FilePath "bun" -ArgumentList "dev" -WorkingDirectory $editorDir

Write-Host "Waiting for editor to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Open browser
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3002"

Start-Sleep -Seconds 5
Write-Host ""
Write-Host "Ready! Editor: http://localhost:3002 | Relay: ws://localhost:3100" -ForegroundColor Green
