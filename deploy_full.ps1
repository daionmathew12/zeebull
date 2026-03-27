# Full Deployment Script for Resort Management System
# This script packages and deploys Backend, Dashboard, and Userend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Resort Management - Full Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Paths
$baseDir = "C:\releasing\New Orchid"
$backendDir = "$baseDir\ResortApp"
$dashboardDir = "$baseDir\dasboard"
$userendDir = "$baseDir\userend"

# Deployment files
$backendZip = "$baseDir\backend_deploy.zip"
$dashboardZip = "$baseDir\dashboard_deploy.zip"
$userendZip = "$baseDir\userend_deploy.zip"

# Server details
$serverIP = "34.134.50.147"
$username = "basilabrahamaby"
$sshKey = "$env:USERPROFILE\.ssh\gcp_key"

Write-Host "`n[1/6] Building Dashboard (React)..." -ForegroundColor Yellow
Set-Location $dashboardDir
if (Test-Path "node_modules") {
    Write-Host "  - node_modules exists, skipping npm install" -ForegroundColor Gray
} else {
    Write-Host "  - Installing dependencies..." -ForegroundColor Gray
    npm install --legacy-peer-deps
}
Write-Host "  - Building production bundle..." -ForegroundColor Gray
if (Test-Path "$dashboardDir\build") {
    Remove-Item -Recurse -Force "$dashboardDir\build"
}
npm run build

Write-Host "`n[2/6] Building Userend (React)..." -ForegroundColor Yellow
Set-Location $userendDir
if (Test-Path "node_modules") {
    Write-Host "  - node_modules exists, skipping npm install" -ForegroundColor Gray
} else {
    Write-Host "  - Installing dependencies..." -ForegroundColor Gray
    npm install --legacy-peer-deps
}
Write-Host "  - Building production bundle..." -ForegroundColor Gray
npm run build
# Write-Host "Skipping Userend build..."

Write-Host "`n[3/6] Creating deployment packages..." -ForegroundColor Yellow
Set-Location $baseDir

# Package Backend (Excluding venv, .env, __pycache__)
Write-Host "  - Packaging ResortApp (Skipping venv, .env)..." -ForegroundColor Gray
# Ensure main.py exists in app/ for service compatibility
if (Test-Path "$backendDir\main.py") {
    Copy-Item "$backendDir\main.py" "$backendDir\app\main.py" -Force
}

if (Test-Path $backendZip) { Remove-Item $backendZip -Force }
Get-ChildItem -Path $backendDir -Exclude "venv", "__pycache__", ".git", ".env", ".idea", ".vscode", "*.log", "*.txt" | Compress-Archive -DestinationPath $backendZip -CompressionLevel Optimal

# Package Dashboard build
Write-Host "  - Packaging Dashboard build..." -ForegroundColor Gray
if (Test-Path $dashboardZip) { Remove-Item $dashboardZip -Force }
Compress-Archive -Path "$dashboardDir\build\*" -DestinationPath $dashboardZip -CompressionLevel Optimal

# Package Userend build
Write-Host "  - Packaging Userend build..." -ForegroundColor Gray
if (Test-Path $userendZip) { Remove-Item $userendZip -Force }
Compress-Archive -Path "$userendDir\build\*" -DestinationPath $userendZip -CompressionLevel Optimal

Write-Host "`n[4/6] Uploading to server..." -ForegroundColor Yellow
Write-Host "  - Uploading backend..." -ForegroundColor Gray
scp -i $sshKey $backendZip "${username}@${serverIP}:~/orchid-repo/"

Write-Host "  - Uploading dashboard..." -ForegroundColor Gray
scp -i $sshKey $dashboardZip "${username}@${serverIP}:~/orchid-repo/"

Write-Host "  - Uploading userend..." -ForegroundColor Gray
scp -i $sshKey $userendZip "${username}@${serverIP}:~/orchid-repo/"

Write-Host "  - Uploading helper scripts..." -ForegroundColor Gray
scp -i $sshKey "$baseDir\extract_fixed.py" "${username}@${serverIP}:~/orchid-repo/"
scp -i $sshKey "$baseDir\fix_paths.py" "${username}@${serverIP}:~/orchid-repo/"
scp -i $sshKey "$baseDir\update_nginx.sh" "${username}@${serverIP}:~/orchid-repo/"

Write-Host "`n[5/6] Deploying on server..." -ForegroundColor Yellow
$deployScript = @"
# Nginx Update
echo '[Server] Updating Nginx Config...'
chmod +x ~/orchid-repo/update_nginx.sh
sudo ~/orchid-repo/update_nginx.sh

# Backend deployment
echo '[Backend] Extracting and deploying...'
sudo rm -rf ~/orchid-repo/ResortApp
python3 ~/orchid-repo/extract_fixed.py ~/orchid-repo/backend_deploy.zip ~/orchid-repo/ResortApp
sudo cp -r ~/orchid-repo/ResortApp/* /var/www/inventory/ResortApp/
# Run fix paths in destination just in case
cd /var/www/inventory/ResortApp/ && sudo python3 ~/orchid-repo/fix_paths.py
echo '[Backend] Running Data Fixes for Bill Display...'
cd /var/www/inventory/ResortApp/ && sudo ./venv/bin/python3 fix_rental_prices_by_id.py
cd /var/www/inventory/ResortApp/ && sudo ./venv/bin/python3 fix_payable_status.py
echo '[Backend] Running Database Migrations...'
cd /var/www/inventory/ResortApp/ && sudo ./venv/bin/python3 migrate_database.py
cd /var/www/inventory/ResortApp/ && sudo ./venv/bin/python3 create_activity_log_table.py

# Userend deployment (Root /inventory)
echo '[Userend] Extracting and deploying...'
sudo rm -rf ~/orchid-repo/userend_build
mkdir -p ~/orchid-repo/userend_build
python3 ~/orchid-repo/extract_fixed.py ~/orchid-repo/userend_deploy.zip ~/orchid-repo/userend_build
# Target: /var/www/html/inventory/
sudo mkdir -p /var/www/html/inventory/
sudo cp -r ~/orchid-repo/userend_build/* /var/www/html/inventory/

# Dashboard deployment (Admin /inventory/admin)
echo '[Dashboard] Extracting and deploying...'
sudo rm -rf ~/orchid-repo/dashboard_build
mkdir -p ~/orchid-repo/dashboard_build
python3 ~/orchid-repo/extract_fixed.py ~/orchid-repo/dashboard_deploy.zip ~/orchid-repo/dashboard_build
# Target: /var/www/resort/Resort_first/dasboard/build/
# Matching Nginx config alias
sudo mkdir -p /var/www/resort/Resort_first/dasboard/build/
sudo rm -rf /var/www/resort/Resort_first/dasboard/build/*
sudo cp -r ~/orchid-repo/dashboard_build/* /var/www/resort/Resort_first/dasboard/build/

# Also copy to legacy path just in case
sudo mkdir -p /var/www/html/orchidadmin/
sudo rm -rf /var/www/html/orchidadmin/*
sudo cp -r ~/orchid-repo/dashboard_build/* /var/www/html/orchidadmin/

# Restart backend service
echo '[Service] Restarting backend...'
sudo systemctl restart inventory-resort.service

echo 'Deployment complete!'
"@

# Strip all carriage returns to avoid "command not found: \r" or "Unit not found: \r" on Linux
$deployScript = [regex]::Replace($deployScript, "\r", "")

ssh -i $sshKey -o StrictHostKeyChecking=no "${username}@${serverIP}" $deployScript

Write-Host "`n[6/6] Verifying deployment..." -ForegroundColor Yellow
$status = ssh -i $sshKey "${username}@${serverIP}" "sudo systemctl status inventory-resort.service --no-pager | head -20"
Write-Host $status

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nYour application is now live at:" -ForegroundColor Cyan
Write-Host "  Backend API: http://34.30.59.169:8011/api" -ForegroundColor Yellow
Write-Host "  Dashboard:   http://34.30.59.169/admin" -ForegroundColor Yellow
Write-Host "  User End:    http://34.30.59.169/resort" -ForegroundColor Yellow

# Cleanup local zip files
Write-Host "`nCleaning up local deployment files..." -ForegroundColor Gray
Remove-Item $backendZip -Force -ErrorAction SilentlyContinue
Remove-Item $dashboardZip -Force -ErrorAction SilentlyContinue
Remove-Item $userendZip -Force -ErrorAction SilentlyContinue

Write-Host "`nDone!" -ForegroundColor Green
