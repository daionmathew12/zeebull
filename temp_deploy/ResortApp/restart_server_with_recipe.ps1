# PowerShell script to restart server with recipe support
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Restarting Server with Recipe Support" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Kill existing Python processes
Write-Host "`n1. Stopping existing Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   ✓ Python processes stopped" -ForegroundColor Green

# Step 2: Create database tables
Write-Host "`n2. Creating database tables..." -ForegroundColor Yellow
python create_recipe_tables.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Tables created/verified" -ForegroundColor Green
} else {
    Write-Host "   ⚠ Warning: Table creation had issues" -ForegroundColor Yellow
}

# Step 3: Activate virtual environment and start server
Write-Host "`n3. Starting server..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\activate.ps1") {
    .\venv\Scripts\activate.ps1
    Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green
}

Write-Host "`nStarting FastAPI server..." -ForegroundColor Cyan
Write-Host "   Watch for these messages:" -ForegroundColor Yellow
Write-Host "   - '✅ Recipe router imported successfully'" -ForegroundColor Green
Write-Host "   - '✅ Recipe router registered in app.main'" -ForegroundColor Green
Write-Host "`nIf you see ❌ ERROR messages, share them!" -ForegroundColor Red
Write-Host "`nServer will start on: http://localhost:8011" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start server (this will block)
python main.py



