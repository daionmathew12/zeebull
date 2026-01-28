$ErrorActionPreference = "Stop"
$server = "basilabrahamaby@34.30.59.169"
$key = "$env:USERPROFILE\.ssh\gcp_key"
$baseDir = "C:\releasing\New Orchid\ResortApp"
$remoteBase = "/var/www/inventory/ResortApp"

$files = @(
    "app/main.py",
    "app/api/report.py",
    "app/api/notification.py",
    "app/curd/notification.py",
    "app/models/notification.py",
    "app/schemas/notification.py",
    "app/models/foodorder.py",
    "app/api/food_orders.py"
)

foreach ($file in $files) {
    $localPath = Join-Path $baseDir $file
    $remotePath = "$remoteBase/$file"
    Write-Host "Uploading $file..."
    scp -i $key $localPath "${server}:/home/basilabrahamaby/temp_file"
    ssh -i $key -o StrictHostKeyChecking=no $server "sudo cp /home/basilabrahamaby/temp_file $remotePath && sudo chown basilabrahamaby:basilabrahamaby $remotePath"
}

Write-Host "Restarting service..."
ssh -i $key -o StrictHostKeyChecking=no $server "sudo systemctl restart inventory-resort.service"
Write-Host "Done."
