$pem = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "basilabrahamaby@34.134.50.147"

Write-Host "Uploading verify script..." -ForegroundColor Cyan
scp -o StrictHostKeyChecking=no -i $pem "c:\releasing\New Orchid\verify_db_state.py" "${remote}:~/verify_db_state.py"

Write-Host "Running verification..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i $pem $remote "cd /var/www/zeebull/ResortApp && sudo ./venv/bin/python3 ~/verify_db_state.py"
