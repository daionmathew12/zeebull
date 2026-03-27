$ErrorActionPreference = "Stop"
$pem = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "basilabrahamaby@34.134.50.147"

$files = @(
    "app/api/inventory.py",
    "app/api/recipe.py",
    "app/api/stock_reconciliation.py",
    "app/api/comprehensive_reports.py",
    "app/curd/inventory.py"
)

foreach ($file in $files) {
    $localPath = "c:\releasing\New Orchid\ResortApp\$file"
    $remoteBase = ($file -split "/")[-1]
    
    Write-Host "Uploading $file..."
    scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $pem $localPath "${remote}:~/$remoteBase"
    
    Write-Host "Patching $file..."
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $pem $remote "sudo cp ~/$remoteBase /var/www/zeebull/ResortApp/$file"
}

Write-Host "Restarting Service..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $pem $remote "sudo systemctl restart zeebull.service"

Write-Host "Done! Backend Patches Applied."
