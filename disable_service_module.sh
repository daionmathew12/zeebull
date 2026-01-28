#!/bin/bash
set -e

MAIN_FILE="/var/www/inventory/ResortApp/main.py"

echo "Backing up main.py..."
cp $MAIN_FILE "${MAIN_FILE}.bak_service_disable"

echo "Disabling Service Module..."
# Comment out the import '    service,'
sed -i 's/    service,/#    service,/g' $MAIN_FILE

# Comment out the router include 'app.include_router(service.router'
sed -i 's/app.include_router(service.router/# app.include_router(service.router/g' $MAIN_FILE

echo "Checking changes..."
grep "service," $MAIN_FILE
grep "service.router" $MAIN_FILE

echo "Restarting Service..."
sudo systemctl restart inventory-resort.service

echo "Done."
