$ErrorActionPreference = "Stop"
$serverIP = "34.30.59.169"
$username = "basilabrahamaby"
$sshKey = "$env:USERPROFILE\.ssh\gcp_key"
$localScript = "c:\releasing\New Orchid\ResortApp\debug_checkout_request.py"

Write-Host "Uploading debug script..."
scp -i $sshKey $localScript "${username}@${serverIP}:~/debug_checkout_request.py"

Write-Host "Running debug script on server..."
ssh -i $sshKey "${username}@${serverIP}" "cd /var/www/inventory/ResortApp && sudo ./venv/bin/python3 ~/debug_checkout_request.py"
