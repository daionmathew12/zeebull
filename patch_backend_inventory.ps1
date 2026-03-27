$ErrorActionPreference = "Stop"
$pem = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "basilabrahamaby@34.134.50.147"
$localFile = "c:\releasing\New Orchid\ResortApp\app\api\inventory.py"

Write-Host "Uploading inventory.py..."
scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $pem $localFile "${remote}:~/inventory.py"

Write-Host "Patching and Restarting..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $pem $remote "sudo cp ~/inventory.py /var/www/zeebull/ResortApp/app/api/inventory.py && sudo systemctl restart zeebull.service"

Write-Host "Done! Inventory Backend Patched."
