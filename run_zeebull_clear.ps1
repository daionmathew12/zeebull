$ErrorActionPreference = "Stop"
$pem = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "basilabrahamaby@34.171.13.80"

Write-Host "1. Uploading zeebulldb cleanup script to server..." -ForegroundColor Cyan
scp -o StrictHostKeyChecking=no -i $pem "c:\releasing\New Orchid\clear_zeebulldb.py" "${remote}:~/clear_zeebulldb.py"

Write-Host "2. Execution on Server..." -ForegroundColor Yellow
$cmd = "sudo cp ~/clear_zeebulldb.py /var/www/inventory/ResortApp/ && cd /var/www/inventory/ResortApp && sudo ./venv/bin/python3 clear_zeebulldb.py"
ssh -o StrictHostKeyChecking=no -i $pem $remote $cmd

Write-Host "`nAll Done!" -ForegroundColor Green
