#!/bin/bash
set -e

echo '[Backend] Extracting backend_deploy_orchid.zip...'
rm -rf ~/ResortApp_Orchid
mkdir -p ~/ResortApp_Orchid
unzip -o ~/backend_deploy_orchid.zip -d ~/ResortApp_Orchid

echo "Source: /home/basilabrahamaby/ResortApp_Orchid/app/api/reports.py"
ls -l /home/basilabrahamaby/ResortApp_Orchid/app/api/reports.py

echo "Destination BEFORE copy: /var/www/inventory/ResortApp/app/api/reports.py"
ls -l /var/www/inventory/ResortApp/app/api/reports.py

echo '[Backend] Force Copying files...'
# Use -f to force and -r for recursive
sudo cp -rf /home/basilabrahamaby/ResortApp_Orchid/* /var/www/inventory/ResortApp/

echo "Destination AFTER copy: /var/www/inventory/ResortApp/app/api/reports.py"
ls -l /var/www/inventory/ResortApp/app/api/reports.py

echo '[Service] Restarting inventory-resort.service...'
sudo systemctl restart inventory-resort.service

echo 'Orchid Backend Deployment Complete (Target: inventory-resort) - Force Copy.'
