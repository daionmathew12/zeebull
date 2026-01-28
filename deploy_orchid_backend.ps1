$ErrorActionPreference = "Stop"
$baseDir = "C:\releasing\New Orchid"
$backendDir = "$baseDir\ResortApp"
$backendZip = "$baseDir\backend_deploy_orchid.zip"
$remoteScript = "$baseDir\remote_deploy.sh"
$serverIP = "34.30.59.169"
$username = "basilabrahamaby"
$sshKey = "$env:USERPROFILE\.ssh\gcp_key"

Write-Host "Packaging Orchid Backend..."
if (Test-Path $backendZip) { Remove-Item $backendZip -Force }
Get-ChildItem -Path $backendDir -Exclude "venv", "__pycache__", ".git", ".env", ".idea", ".vscode" | Compress-Archive -DestinationPath $backendZip -CompressionLevel Optimal

Write-Host "Uploading Backend & Script..."
scp -i $sshKey $backendZip "${username}@${serverIP}:~/backend_deploy_orchid.zip"
scp -i $sshKey $remoteScript "${username}@${serverIP}:~/remote_deploy.sh"

Write-Host "Executing Deployment on Server..."
# Execute the uploaded script, using sed to convert line endings if dos2unix is missing
ssh -i $sshKey -o StrictHostKeyChecking=no "${username}@${serverIP}" "chmod +x ~/remote_deploy.sh && sed -i 's/\r$//' ~/remote_deploy.sh && ~/remote_deploy.sh"

Write-Host "Deployment Process Finished."
