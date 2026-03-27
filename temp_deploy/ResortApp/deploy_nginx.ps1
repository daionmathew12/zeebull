# Deploy updated nginx configuration to server
Write-Host "Deploying nginx configuration to server..." -ForegroundColor Green

$sshKey = "C:\Users\pro\.ssh\gcp_key"
$server = "basilabrahamabdulkader@34.93.186.233"

# Copy nginx.conf to server
Write-Host "Copying nginx.conf to server..." -ForegroundColor Yellow
scp -i $sshKey nginx.conf "${server}:/tmp/nginx.conf"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to copy nginx.conf to server" -ForegroundColor Red
    exit 1
}

# Update nginx config on server
Write-Host "Updating nginx configuration on server..." -ForegroundColor Yellow
$commands = @"
echo 'Backing up current nginx config...'
sudo cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.backup.`$(date +%Y%m%d_%H%M%S)

echo 'Installing new nginx config...'
sudo cp /tmp/nginx.conf /etc/nginx/sites-enabled/default

echo 'Testing nginx configuration...'
sudo nginx -t

if [ `$? -eq 0 ]; then
    echo 'Configuration valid. Reloading nginx...'
    sudo systemctl reload nginx
    echo 'Nginx reloaded successfully!'
else
    echo 'Configuration test failed. Restoring backup...'
    sudo cp /etc/nginx/sites-enabled/default.backup.* /etc/nginx/sites-enabled/default
    echo 'Backup restored. Please check the configuration.'
    exit 1
fi
"@

ssh -i $sshKey $server $commands

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDeployment complete! The /orchidadmin route should now work correctly." -ForegroundColor Green
    Write-Host "Try refreshing your browser at: http://teqmates.co.in/orchidadmin/dashboard" -ForegroundColor Cyan
} else {
    Write-Host "`nDeployment failed. Please check the error messages above." -ForegroundColor Red
}
