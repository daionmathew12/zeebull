$ErrorActionPreference = "Stop"

$baseDir = "C:\releasing\New Orchid"
$backendDir = "$baseDir\ResortApp"
$dashboardDir = "$baseDir\dasboard"
$userendDir = "$baseDir\userend"

$backendZip = "$baseDir\backend_wipe.zip"
$dashboardZip = "$baseDir\dashboard_wipe.zip"
$userendZip = "$baseDir\userend_wipe.zip"

$serverIP = "34.134.50.147"
$username = "basilabrahamaby"
$sshKey = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "${username}@${serverIP}"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Zeebull - WIPE AND FULL REDEPLOY" -ForegroundColor Red -BackgroundColor Black
Write-Host "Target: $serverIP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── Step 0: Backup .env and WIPE Server ──────────────────────────────────
Write-Host "`n[0/6] Cleaning server (DB and Files)..." -ForegroundColor Yellow

$wipeScript = @"
set -e
echo '--- Stopping Service ---'
sudo systemctl stop zeebull.service || true

echo '--- Backing up .env ---'
if [ -f /var/www/zeebull/ResortApp/.env ]; then
    cp /var/www/zeebull/ResortApp/.env ~/zeebull_env_backup
    echo '✓ .env backed up.'
fi

echo '--- Dropping Database ---'
# Use WITH (FORCE) for PostgreSQL 13+ to drop connections automatically
sudo -u postgres psql -c 'DROP DATABASE IF EXISTS zeebulldb WITH (FORCE);'
sudo -u postgres psql -c 'CREATE DATABASE zeebulldb;'
sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE zeebulldb TO orchid_user;'
echo '✓ Database recreated.'

echo '--- Clearing Web Directories ---'
sudo rm -rf /var/www/zeebull/ResortApp
sudo rm -rf /var/www/zeebull/dashboard
sudo rm -rf /var/www/zeebull/userend
sudo mkdir -p /var/www/zeebull/ResortApp /var/www/zeebull/dashboard /var/www/zeebull/userend /var/log/orchid
sudo chown -R basilabrahamaby:www-data /var/www/zeebull/
sudo chown -R basilabrahamaby:www-data /var/log/orchid/
sudo chmod -R 775 /var/www/zeebull/
sudo chmod -R 775 /var/log/orchid/
echo '✓ Directories cleared.'
"@

$wipeScript = [regex]::Replace($wipeScript, "\r", "")
ssh -i $sshKey -o StrictHostKeyChecking=no $remote $wipeScript
if ($LASTEXITCODE -ne 0) { throw "Wipe failed on server!" }

Write-Host "✓ Wipe successful. Proceeding with buildings..." -ForegroundColor Green

# ── Step 1: Build Dashboard ───────────────────────────────────────────────
Write-Host "`n[1/6] Building Dashboard (React)..." -ForegroundColor Yellow
Set-Location $dashboardDir
$env:CI = "false"
npm run build
if ($LASTEXITCODE -ne 0) { throw "Dashboard build failed!" }

# ── Step 2: Build Userend ────────────────────────────────────────────────
Write-Host "`n[2/6] Building Userend (React)..." -ForegroundColor Yellow
Set-Location $userendDir
$env:CI = "false"
npm run build
if ($LASTEXITCODE -ne 0) { throw "Userend build failed!" }

Set-Location $baseDir

# ── Step 3: Package ──────────────────────────────────────────────────────
Write-Host "`n[3/6] Packaging deployment files..." -ForegroundColor Yellow

# Backend
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
Write-Host "`n[4/6] Uploading to server ($serverIP)..." -ForegroundColor Yellow
scp -i $sshKey -o StrictHostKeyChecking=no $backendZip "${remote}:~/backend_wipe.zip"
scp -i $sshKey -o StrictHostKeyChecking=no $dashboardZip "${remote}:~/dashboard_wipe.zip"
scp -i $sshKey -o StrictHostKeyChecking=no $userendZip "${remote}:~/userend_wipe.zip"
scp -i $sshKey -o StrictHostKeyChecking=no "$baseDir\db_init.py" "${remote}:~/db_init.py"

# ── Step 5: Extract and Initialize ─────────────────────────────────────
Write-Host "`n[5/6] Extracting and Initializing on server..." -ForegroundColor Yellow

$deployScript = @"
set -e

echo '--- Extracting Backend ---'
unzip -o ~/backend_wipe.zip -d /var/www/zeebull/ResortApp/

echo '--- Extracting Dashboard ---'
unzip -o ~/dashboard_wipe.zip -d /var/www/zeebull/dashboard/

echo '--- Extracting Userend ---'
unzip -o ~/userend_wipe.zip -d /var/www/zeebull/userend/

echo '--- Restoring .env ---'
if [ -f ~/zeebull_env_backup ]; then
    cp ~/zeebull_env_backup /var/www/zeebull/ResortApp/.env
else
    echo 'Warning: ~/zeebull_env_backup not found!'
fi

echo '--- Setting up Python Environment ---'
cd /var/www/zeebull/ResortApp
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo '--- Initializing Database ---'
./venv/bin/python3 ~/db_init.py

echo '--- Permissions ---'
sudo chown -R $username:www-data /var/www/zeebull/
sudo chmod -R 775 /var/www/zeebull/
"@

$deployScript = [regex]::Replace($deployScript, "\r", "")
ssh -i $sshKey -o StrictHostKeyChecking=no $remote $deployScript

# ── Step 6: Restart Services ──────────────────────────────────────────
Write-Host "`n[6/6] Restarting Services..." -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no $remote "sudo systemctl restart zeebull.service && sudo systemctl reload nginx"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "REDPLOYMENT COMPLETED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Dashboard:  https://teqmates.com/zeebulladmin/" -ForegroundColor Cyan
Write-Host "  User End:   https://teqmates.com/zeebull/" -ForegroundColor Cyan

# Cleanup local zips
Remove-Item $backendZip -Force -ErrorAction SilentlyContinue
Remove-Item $dashboardZip -Force -ErrorAction SilentlyContinue
Remove-Item $userendZip -Force -ErrorAction SilentlyContinue
