$ErrorActionPreference = "Stop"
$localFile = "C:\releasing\New Orchid\ResortApp\app\api\report.py"
$remotePath = "/home/basilabrahamaby/report.py"
$finalPath = "/var/www/inventory/ResortApp/app/api/report.py"
$server = "basilabrahamaby@34.30.59.169"
$key = "$env:USERPROFILE\.ssh\gcp_key"

Write-Host "Uploading report.py directly..."
scp -i $key $localFile "${server}:${remotePath}"

Write-Host "Moving to final destination and restarting..."
ssh -i $key -o StrictHostKeyChecking=no $server "sudo cp ${remotePath} ${finalPath} && sudo systemctl restart inventory-resort.service"

Write-Host "Done."
