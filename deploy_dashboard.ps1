$ErrorActionPreference = "Stop"

$pem = "$env:USERPROFILE\.ssh\gcp_key"
$remote = "basilabrahamaby@34.30.59.169"

Write-Host "1. Creating Dashboard directory on server..."
ssh -o StrictHostKeyChecking=no -i $pem $remote "sudo mkdir -p /var/www/html/orchidadmin"

Write-Host "2. Uploading Dashboard build files..."
ssh -o StrictHostKeyChecking=no -i $pem $remote "rm -rf ~/dashboard_build"
scp -r -o StrictHostKeyChecking=no -i $pem "c:\releasing\New Orchid\dasboard\build" "${remote}:~/dashboard_build"

Write-Host "3. Moving files to web directory..."
ssh -o StrictHostKeyChecking=no -i $pem $remote "sudo rm -rf /var/www/html/orchidadmin/* && sudo cp -r ~/dashboard_build/* /var/www/html/orchidadmin/ && sudo chmod -R 755 /var/www/html/orchidadmin/"

Write-Host "4. Configuring Nginx for Dashboard..."
$nginxConfig = @'
    location /inventoryadmin/ {
        alias /var/www/html/inventoryadmin/;
        try_files $uri $uri/ /inventoryadmin/index.html;
        add_header Cache-Control "no-cache, must-revalidate";
    }
'@

# Upload config snippet
$nginxConfig | Out-File -FilePath "c:\releasing\New Orchid\dashboard_nginx.conf" -Encoding ASCII

Write-Host "Dashboard deployed! Access at: https://teqmates.com/orchid/admin/"
Write-Host "`nNote: You'll need to manually add the Nginx location block to /etc/nginx/sites-enabled/pomma"
