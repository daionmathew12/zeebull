# PowerShell script to restart the backend server
Write-Host "Stopping any running Python processes on port 8011..." -ForegroundColor Yellow

# Find and kill processes using port 8011
$processes = Get-NetTCPConnection -LocalPort 8011 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($proc_id in $processes) {
    if ($proc_id) {
        Write-Host "Killing process $proc_id on port 8011..." -ForegroundColor Yellow
        Stop-Process -Id $proc_id -Force -ErrorAction SilentlyContinue
    }
}

# Wait a moment
Start-Sleep -Seconds 2

Write-Host "`nStarting backend server..." -ForegroundColor Green
Write-Host "Watch for these messages:" -ForegroundColor Cyan
Write-Host "  ✅ Recipe router imported successfully in app.main" -ForegroundColor Green
Write-Host "  ✅ Recipe router registered in app.main with X routes" -ForegroundColor Green
Write-Host "`nIf you see error messages instead, share them." -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Gray

# Start the server
$Env:PYTHONIOENCODING = "utf-8"
python main.py
