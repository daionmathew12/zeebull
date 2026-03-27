$ErrorActionPreference = "Stop"
$serverIP = "34.30.59.169"
$username = "basilabrahamaby"
$sshKey = "$env:USERPROFILE\.ssh\gcp_key"
$localScript = "c:\releasing\New Orchid\ResortApp\clean_103_inventory.py"

Write-Host "Uploading cleanup script..."
scp -i $sshKey $localScript "${username}@${serverIP}:~/clean_103_inventory.py"

Write-Host "Running cleanup script on server..."
ssh -i $sshKey "${username}@${serverIP}" "cd /var/www/inventory/ResortApp && sudo ./venv/bin/python3 ~/clean_103_inventory.py"
