$pem = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "basilabrahamaby@34.134.50.147"

Write-Host "=== Checking zeebull.service status ===" -ForegroundColor Cyan
ssh -o StrictHostKeyChecking=no -i $pem $remote "sudo systemctl status zeebull.service --no-pager -l | head -40"

Write-Host "`n=== Checking recent logs ===" -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i $pem $remote "sudo journalctl -u zeebull.service -n 30 --no-pager"
