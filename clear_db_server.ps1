$pem = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "basilabrahamaby@34.134.50.147"

Write-Host "" 
Write-Host "=== CLEARING SERVER DATABASE (zeebulldb) ===" -ForegroundColor Red
Write-Host ""

Write-Host "1. Uploading clear_zeebulldb.py to server..." -ForegroundColor Cyan
scp -o StrictHostKeyChecking=no -i $pem "c:\releasing\New Orchid\clear_zeebulldb.py" "${remote}:~/clear_zeebulldb.py"

Write-Host ""
Write-Host "2. Running DB clear on server..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i $pem $remote "cd /var/www/zeebull/ResortApp && sudo ./venv/bin/python3 ~/clear_zeebulldb.py"

Write-Host ""
Write-Host "3. Restarting zeebull.service..." -ForegroundColor Cyan
ssh -o StrictHostKeyChecking=no -i $pem $remote "sudo systemctl restart zeebull.service"

Write-Host ""
Write-Host "=== DATABASE CLEAR COMPLETE! ===" -ForegroundColor Green
Write-Host "Login: admin@orchid.com / admin123" -ForegroundColor White
