$ErrorActionPreference = "Stop"

$baseDir = "C:\releasing\New Orchid"
$backendDir = "$baseDir\ResortApp"
$dashboardDir = "$baseDir\dasboard"
$userendDir = "$baseDir\userend"

$backendZip = "$baseDir\backend_deploy_now.zip"
$dashboardZip = "$baseDir\dashboard_deploy_now.zip"
$userendZip = "$baseDir\userend_deploy_now.zip"

$serverIP = "34.134.50.147"
$username = "basilabrahamaby"
$sshKey = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "${username}@${serverIP}"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Resort Management - Full Deployment" -ForegroundColor Cyan
Write-Host "Target: $serverIP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── Step 1: Build Dashboard ───────────────────────────────────────────────
Write-Host "`n[1/5] Building Dashboard (React)..." -ForegroundColor Yellow
Set-Location $dashboardDir
$env:CI = "false"
npm run build
if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed!" }

# ── Step 2: Build Userend ────────────────────────────────────────────────
Write-Host "`n[2/5] Building Userend (React)..." -ForegroundColor Yellow
Set-Location $userendDir
$env:CI = "false"
npm run build
if ($LASTEXITCODE -ne 0) { throw "Userend build failed!" }

Set-Location $baseDir

# ── Step 3: Package ──────────────────────────────────────────────────────
Write-Host "`n[3/5] Packaging deployment files..." -ForegroundColor Yellow

# Backend (exclude venv, __pycache__, .env, .git)
Write-Host "  - Packaging Backend..." -ForegroundColor Gray
if (Test-Path $backendZip) { Remove-Item $backendZip -Force }
Get-ChildItem -Path $backendDir -Exclude "venv", "__pycache__", ".git", ".env", ".idea", ".vscode", "*.log" | `
    Compress-Archive -DestinationPath $backendZip -CompressionLevel Optimal

# Dashboard build
Write-Host "  - Packaging Dashboard build..." -ForegroundColor Gray
if (Test-Path $dashboardZip) { Remove-Item $dashboardZip -Force }
Compress-Archive -Path "$dashboardDir\build\*" -DestinationPath $dashboardZip -CompressionLevel Optimal

# Userend build
Write-Host "  - Packaging Userend build..." -ForegroundColor Gray
if (Test-Path $userendZip) { Remove-Item $userendZip -Force }
Compress-Archive -Path "$userendDir\build\*" -DestinationPath $userendZip -CompressionLevel Optimal

# ── Step 4: Upload ───────────────────────────────────────────────────────
Write-Host "`n[4/5] Uploading to server ($serverIP)..." -ForegroundColor Yellow
Write-Host "  - Uploading backend..." -ForegroundColor Gray
scp -i $sshKey -o StrictHostKeyChecking=no $backendZip "${remote}:~/backend_deploy_now.zip"

Write-Host "  - Uploading dashboard..." -ForegroundColor Gray
scp -i $sshKey -o StrictHostKeyChecking=no $dashboardZip "${remote}:~/dashboard_deploy_now.zip"

Write-Host "  - Uploading userend..." -ForegroundColor Gray
scp -i $sshKey -o StrictHostKeyChecking=no $userendZip "${remote}:~/userend_deploy_now.zip"

# ── Step 5: Deploy on server ─────────────────────────────────────────────
Write-Host "`n[5/5] Deploying on server..." -ForegroundColor Yellow

$deployScript = @"
set -e

echo '=== [Backend] Extracting ==='
rm -rf ~/ResortApp_Deploy
mkdir -p ~/ResortApp_Deploy
unzip -o ~/backend_deploy_now.zip -d ~/ResortApp_Deploy || python3 -m zipfile -e ~/backend_deploy_now.zip ~/ResortApp_Deploy

echo '=== [Backend] Deploying ==='
sudo cp -r ~/ResortApp_Deploy/* /var/www/zeebull/ResortApp/
sudo chown -R www-data:www-data /var/www/zeebull/ResortApp/
sudo chmod -R 755 /var/www/zeebull/ResortApp/

echo '=== [Backend] Running migrations ==='
cd /var/www/zeebull/ResortApp/
sudo ./venv/bin/python3 migrate_database.py || echo 'migrate_database.py skipped or failed'

echo '=== [Userend] Extracting ==='
rm -rf ~/userend_deploy_temp
mkdir -p ~/userend_deploy_temp
unzip -o ~/userend_deploy_now.zip -d ~/userend_deploy_temp

echo '=== [Userend] Deploying ==='
sudo rm -rf /var/www/zeebull/userend/*
sudo cp -r ~/userend_deploy_temp/* /var/www/zeebull/userend/
sudo chmod -R 755 /var/www/zeebull/userend/

echo '=== [Dashboard] Extracting ==='
rm -rf ~/dashboard_deploy_temp
mkdir -p ~/dashboard_deploy_temp
unzip -o ~/dashboard_deploy_now.zip -d ~/dashboard_deploy_temp

echo '=== [Dashboard] Deploying ==='
sudo rm -rf /var/www/zeebull/dasboard/*
sudo cp -r ~/dashboard_deploy_temp/* /var/www/zeebull/dasboard/
sudo chmod -R 755 /var/www/zeebull/dasboard/

echo '=== [Service] Restarting backend ==='
sudo systemctl restart zeebull.service

echo '=== [Nginx] Reloading ==='
sudo systemctl reload nginx

echo '=== Deployment Complete! ==='
"@

# Strip carriage returns so bash on Linux doesn't choke
$deployScript = [regex]::Replace($deployScript, "\r", "")

ssh -i $sshKey -o StrictHostKeyChecking=no $remote $deployScript

# ── Verify ───────────────────────────────────────────────────────────────
Write-Host "`nVerifying service status..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
ssh -i $sshKey -o StrictHostKeyChecking=no $remote "sudo systemctl status zeebull.service --no-pager | head -20"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Dashboard:  https://teqmates.com/zeebulladmin/" -ForegroundColor Cyan
Write-Host "  User End:   https://teqmates.com/zeebull/" -ForegroundColor Cyan

# Cleanup
Remove-Item $backendZip -Force -ErrorAction SilentlyContinue
Remove-Item $dashboardZip -Force -ErrorAction SilentlyContinue
Remove-Item $userendZip -Force -ErrorAction SilentlyContinue
