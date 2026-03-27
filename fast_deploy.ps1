$ErrorActionPreference = "Stop"

$baseDir = "C:\releasing\New Orchid"
$backendZip = "$baseDir\resortapp_deploy.zip"
$dashboardZip = "$baseDir\dashboard_deploy.zip"
$userendZip = "$baseDir\userend_deploy.zip"

$serverIP = "34.134.50.147"
$username = "basilabrahamaby"
$sshKey = "$env:USERPROFILE\.ssh\gcp_key"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Resort Management - Fast Deployment (Upload & Deploy Only)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if Zips exist
if (-not (Test-Path $backendZip)) { Write-Error "Backend zip not found!" }
if (-not (Test-Path $dashboardZip)) { Write-Error "Dashboard zip not found!" }
if (-not (Test-Path $userendZip)) { Write-Error "Userend zip not found!" }

Write-Host "`n[1/3] Uploading to server..." -ForegroundColor Yellow
Write-Host "  - Uploading backend..." -ForegroundColor Gray
scp -i $sshKey $backendZip "${username}@${serverIP}:~/orchid-repo/"

Write-Host "  - Uploading dashboard..." -ForegroundColor Gray
scp -i $sshKey $dashboardZip "${username}@${serverIP}:~/orchid-repo/"

Write-Host "  - Uploading userend..." -ForegroundColor Gray
scp -i $sshKey $userendZip "${username}@${serverIP}:~/orchid-repo/"

Write-Host "  - Uploading helper scripts..." -ForegroundColor Gray
# Ensure these exist locally first, usually they do from previous context
if (Test-Path "$baseDir\extract_fixed.py") { scp -i $sshKey "$baseDir\extract_fixed.py" "${username}@${serverIP}:~/orchid-repo/" }
if (Test-Path "$baseDir\fix_paths.py") { scp -i $sshKey "$baseDir\fix_paths.py" "${username}@${serverIP}:~/orchid-repo/" }
if (Test-Path "$baseDir\update_nginx.sh") { scp -i $sshKey "$baseDir\update_nginx.sh" "${username}@${serverIP}:~/orchid-repo/" }

Write-Host "`n[2/3] Deploying on server..." -ForegroundColor Yellow
$deployScript = @"
# Ensure helper scripts are executable
chmod +x ~/orchid-repo/update_nginx.sh

# 1. Backend Deployment
# 1. Backend Deployment
echo '[Backend] Extracting and deploying...'
sudo rm -rf ~/orchid-repo/ResortApp_temp
unzip -q -o ~/orchid-repo/resortapp_deploy.zip -d ~/orchid-repo/ResortApp_temp
# Copy files into the existing directory, preserving venv and .env
sudo cp -rv ~/orchid-repo/ResortApp_temp/ResortApp/* /var/www/inventory/ResortApp/
sudo rm -rf ~/orchid-repo/ResortApp_temp

# Fix permissions
sudo chown -R www-data:www-data /var/www/inventory/ResortApp

echo '[Backend] Running Migrations & Fixes...'
cd /var/www/inventory/ResortApp/
# Install dependencies if requirements changed (optional, skipping for speed unless needed)
# sudo pip install -r requirements.txt
sudo ./venv/bin/python3 migrate_database.py
sudo ./venv/bin/python3 create_activity_log_table.py
# Run these specific fixes as requested in previous full deploy
if [ -f "fix_rental_prices_by_id.py" ]; then sudo ./venv/bin/python3 fix_rental_prices_by_id.py; fi
if [ -f "fix_payable_status.py" ]; then sudo ./venv/bin/python3 fix_payable_status.py; fi

# 2. Userend Deployment
echo '[Userend] Extracting and deploying...'
sudo rm -rf ~/orchid-repo/userend_build_temp
unzip -q -o ~/orchid-repo/userend_deploy.zip -d ~/orchid-repo/userend_build_temp
sudo mkdir -p /var/www/html/inventory/
sudo cp -r ~/orchid-repo/userend_build_temp/* /var/www/html/inventory/
sudo rm -rf ~/orchid-repo/userend_build_temp

# 3. Dashboard Deployment
echo '[Dashboard] Extracting and deploying...'
sudo rm -rf ~/orchid-repo/dashboard_build_temp
unzip -q -o ~/orchid-repo/dashboard_deploy.zip -d ~/orchid-repo/dashboard_build_temp

# Target 1: /var/www/resort/Resort_first/dasboard/build/ (for nginx alias compatibility)
sudo mkdir -p /var/www/resort/Resort_first/dasboard/build/
sudo rm -rf /var/www/resort/Resort_first/dasboard/build/*
sudo cp -r ~/orchid-repo/dashboard_build_temp/* /var/www/resort/Resort_first/dasboard/build/

# Target 2: /var/www/html/orchidadmin/ (Legacy/Safe path)
sudo mkdir -p /var/www/html/orchidadmin/
sudo rm -rf /var/www/html/orchidadmin/*
sudo cp -r ~/orchid-repo/dashboard_build_temp/* /var/www/html/orchidadmin/

sudo rm -rf ~/orchid-repo/dashboard_build_temp

# 4. Restart Services
echo '[Service] Restarting backend...'
sudo systemctl restart inventory-resort.service
echo '[Service] Reloading Nginx...'
sudo systemctl reload nginx

echo 'Deployment complete!'
"@

# Clean up script for transit
$deployScript = [regex]::Replace($deployScript, "\r", "")

ssh -i $sshKey -o StrictHostKeyChecking=no "${username}@${serverIP}" $deployScript

Write-Host "`n[3/3] Verifying service..." -ForegroundColor Yellow
ssh -i $sshKey "${username}@${serverIP}" "sudo systemctl status inventory-resort.service --no-pager | head -10"

Write-Host "`nDEPLOYMENT DONE!" -ForegroundColor Green
