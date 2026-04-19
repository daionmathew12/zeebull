# 🚀 Zeebull Specialized Deployment Script (GCP VM)
# IP: 34.162.60.52
# User: basilabrahamaby
# SSH Key: $env:USERPROFILE\.ssh\gcp_key

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Zeebull Resort Management - GCP Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Configuration
$baseDir = "D:\Zeebull"
$serverIP = "34.162.60.52"
$username = "basilabrahamaby"
$sshKey = "$baseDir\temp_key"
$remoteDest = "/home/$username/zeebull_bundle"

# Local directories
$backendDir = "$baseDir\ResortApp"
$dashboardDir = "$baseDir\dasboard"
$userendDir = "$baseDir\userend"

# Zips
$backendZip = "$baseDir\backend_deploy.zip"
$dashboardZip = "$baseDir\dashboard_deploy.zip"
$userendZip = "$baseDir\userend_deploy.zip"

Write-Host "`n[1/6] Building Admin Dashboard (React)..." -ForegroundColor Yellow
Set-Location $dashboardDir
if (!(Test-Path "node_modules")) {
    Write-Host "  - Installing dashboard dependencies..." -ForegroundColor Gray
    npm install --legacy-peer-deps
}
Write-Host "  - Building dashboard..." -ForegroundColor Gray
if (Test-Path "$dashboardDir\build") { Remove-Item -Recurse -Force "$dashboardDir\build" }
npm run build

Write-Host "`n[2/6] Building User Interface (React)..." -ForegroundColor Yellow
Set-Location $userendDir
if (!(Test-Path "node_modules")) {
    Write-Host "  - Installing userend dependencies..." -ForegroundColor Gray
    npm install --legacy-peer-deps
}
Write-Host "  - Building userend..." -ForegroundColor Gray
if (Test-Path "$userendDir\build") { Remove-Item -Recurse -Force "$userendDir\build" }
npm run build

Write-Host "`n[3/6] Packaging deployment bundles..." -ForegroundColor Yellow
Set-Location $baseDir
if (Test-Path $backendZip) { Remove-Item $backendZip -Force }
if (Test-Path $dashboardZip) { Remove-Item $dashboardZip -Force }
if (Test-Path $userendZip) { Remove-Item $userendZip -Force }

# Backend (Skip venv for speed, we reinstall or preserve on server)
Write-Host "  - Packaging ResortApp..." -ForegroundColor Gray
Get-ChildItem -Path $backendDir -Exclude "venv", "__pycache__", ".git", ".env", ".idea", ".vscode" | Compress-Archive -DestinationPath $backendZip

# Frontend builds
Write-Host "  - Packaging Static Builds..." -ForegroundColor Gray
Compress-Archive -Path "$dashboardDir\build\*" -DestinationPath $dashboardZip
Compress-Archive -Path "$userendDir\build\*" -DestinationPath $userendZip

Write-Host "`n[4/6] Uploading to Google Cloud VM ($serverIP)..." -ForegroundColor Yellow
# Ensure staging dir on server
ssh -i $sshKey -o StrictHostKeyChecking=no "${username}@${serverIP}" "mkdir -p $remoteDest"
scp -i $sshKey $backendZip "${username}@${serverIP}:$remoteDest/"
scp -i $sshKey $dashboardZip "${username}@${serverIP}:$remoteDest/"
scp -i $sshKey $userendZip "${username}@${serverIP}:$remoteDest/"

Write-Host "`n[5/6] Deploying on GCP VM..." -ForegroundColor Yellow
$deployCommand = @"
set -e
echo '[Deploy] Stopping Zeebull Service...'
sudo systemctl stop zeebull.service || true

# Setup Directories
sudo mkdir -p /var/www/zeebull/ResortApp
sudo mkdir -p /var/www/zeebull/dasboard
sudo mkdir -p /var/www/zeebull/userend
sudo mkdir -p /var/www/landing

# Extraction (Using Python's zipfile for safety on Linux)
python3 -c "import zipfile, os; zipfile.ZipFile('$remoteDest/backend_deploy.zip').extractall('/var/www/zeebull/ResortApp')"
python3 -c "import zipfile, os; zipfile.ZipFile('$remoteDest/dashboard_deploy.zip').extractall('/var/www/zeebull/dasboard')"
python3 -c "import zipfile, os; zipfile.ZipFile('$remoteDest/userend_deploy.zip').extractall('/var/www/zeebull/userend')"

# Configuration Restore (If exists)
if [ -f /var/www/zeebull/ResortApp/.env ]; then
    echo '[Deploy] Preserving existing .env...'
else
    echo '[Deploy] Warning: No .env found. Please create one on the server.'
fi

# Permissions
sudo chown -R $username:www-data /var/www/zeebull
sudo chmod -R 775 /var/www/zeebull

# Restart Service
echo '[Deploy] Starting backend service...'
sudo systemctl daemon-reload
sudo systemctl start zeebull.service
sudo systemctl restart nginx

echo '✅ DEPLOYMENT SUCCESSFUL!'
"@

# Normalize line endings for Linux
$deployCommand = [regex]::Replace($deployCommand, "\r", "")

ssh -i $sshKey -o StrictHostKeyChecking=no "${username}@${serverIP}" $deployCommand

Write-Host "`n[6/6] Verifying system status..." -ForegroundColor Yellow
ssh -i $sshKey "${username}@${serverIP}" "sudo systemctl status zeebull.service --no-pager | head -n 10"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "ZEEBULL IS LIVE AT: http://$serverIP" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
