# Script to fix vendor save issue by ensuring clean server restart
Write-Host "=== Fixing Vendor Save Issue ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Kill all Python processes
Write-Host "Step 1: Stopping all Python processes..." -ForegroundColor Yellow
Get-Process | Where-Object {
    ($_.ProcessName -eq "python" -or $_.ProcessName -eq "uvicorn") -and
    ($_.Path -like "*orchid*" -or $_.Path -like "*ResortApp*" -or $_.Path -like "*venv*")
} | ForEach-Object {
    Write-Host "  Stopping PID $($_.Id) - $($_.ProcessName)" -ForegroundColor Gray
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

# Step 2: Kill processes on port 8011
Write-Host "`nStep 2: Freeing port 8011..." -ForegroundColor Yellow
$attempts = 0
do {
    $listening = Get-NetTCPConnection -LocalPort 8011 -ErrorAction SilentlyContinue
    if ($listening) {
        $listening | ForEach-Object {
            $pid = $_.OwningProcess
            Write-Host "  Killing process $pid on port 8011" -ForegroundColor Gray
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
        $attempts++
    }
} while ($listening -and $attempts -lt 5)

Start-Sleep -Seconds 3

# Step 3: Verify port is free
Write-Host "`nStep 3: Verifying port 8011 is free..." -ForegroundColor Yellow
$stillListening = Get-NetTCPConnection -LocalPort 8011 -ErrorAction SilentlyContinue
if ($stillListening) {
    Write-Host "  ⚠️  Port 8011 is still in use!" -ForegroundColor Red
    Write-Host "  Please manually kill these processes:" -ForegroundColor Yellow
    $stillListening | ForEach-Object {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "    PID $($proc.Id) - $($proc.ProcessName) - $($proc.Path)" -ForegroundColor Yellow
        }
    }
    Write-Host "`n  Run: Get-Process python | Stop-Process -Force" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "  ✅ Port 8011 is free!" -ForegroundColor Green
}

# Step 4: Clear Python cache
Write-Host "`nStep 4: Clearing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path "." -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "  ✅ Cache cleared" -ForegroundColor Green

# Step 5: Start server
Write-Host "`nStep 5: Starting server with fixed code..." -ForegroundColor Yellow
Set-Location "C:\releasing\orchid\ResortApp"
$serverProcess = Start-Process -FilePath "venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8011", "--host", "0.0.0.0" `
    -PassThru `
    -NoNewWindow

Write-Host "  Server started with PID: $($serverProcess.Id)" -ForegroundColor Green
Write-Host "  Waiting for server to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 12

# Step 6: Test endpoint
Write-Host "`nStep 6: Testing vendor endpoint..." -ForegroundColor Yellow
$token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjkyNjgzMzV9.MwGGTxTmwXUFSlsn4Nkg-gpY4W_QvcqSgq36eGS3W98"
$body = '{"name":"Test Vendor","company_name":"Test Co","gst_registration_type":"Unregistered","billing_address":"123 Test St","billing_state":"Kerala","is_active":true}'

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8011/api/inventory/vendors" `
        -Method POST `
        -Headers @{"Authorization"=$token; "Content-Type"="application/json"} `
        -Body $body `
        -ErrorAction Stop
    
    Write-Host "  🎉 SUCCESS! Vendor endpoint is working!" -ForegroundColor Green
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "`n✅ Vendor save is now fixed!" -ForegroundColor Green
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Write-Host "  ❌ Still getting $status" -ForegroundColor Red
    Write-Host "`n⚠️  The server may need more time to start." -ForegroundColor Yellow
    Write-Host "  Please check the server console output for:" -ForegroundColor Yellow
    Write-Host "    ✅ Inventory router imported successfully in app.main" -ForegroundColor Cyan
    Write-Host "    ✅ Inventory router registered in app.main with 14 routes" -ForegroundColor Cyan
    Write-Host "`n  If you see these messages, the endpoint should work!" -ForegroundColor Green
}

Write-Host "`n=== Script Complete ===" -ForegroundColor Cyan
Write-Host "Server PID: $($serverProcess.Id)" -ForegroundColor Gray
Write-Host "To stop: Stop-Process -Id $($serverProcess.Id) -Force" -ForegroundColor Gray

