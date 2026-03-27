#!/bin/bash
set -x

# 1. Prepare Extraction
echo "Unzipping updates..."
sudo rm -rf /tmp/zeebull_extract
sudo mkdir -p /tmp/zeebull_extract
sudo unzip -o /tmp/zeebull_deploy_final.zip -d /tmp/zeebull_extract/

# 2. Update Backend
echo "Updating Backend..."
sudo cp -r /tmp/zeebull_extract/ResortApp/* /var/www/zeebull/ResortApp/

# 3. Update User Frontend
echo "Updating User Frontend..."
sudo rm -rf /var/www/zeebull/userend/*
sudo cp -r /tmp/zeebull_extract/userend/* /var/www/zeebull/userend/

# 4. Update Dashboard (handle dasboard vs dashboard name)
echo "Updating Dashboard..."
sudo rm -rf /var/www/zeebull/dasboard/*
sudo cp -r /tmp/zeebull_extract/dashboard/* /var/www/zeebull/dasboard/

# 5. Database migration
echo "Running database migration..."
cd /var/www/zeebull/ResortApp
sudo ./venv/bin/python3 migrate_db_server.py || echo "Migration failed"

# 6. Final Permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data /var/www/zeebull
sudo chmod -R 775 /var/www/zeebull

# 7. Restart Backend
echo "Restarting Backend Service..."
sudo systemctl restart zeebull
sudo systemctl status zeebull --no-pager

# Clean up
sudo rm -rf /tmp/zeebull_extract

echo "Production update complete!"
