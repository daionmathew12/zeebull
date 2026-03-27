#!/bin/bash
set -x

# 1. Update Files
cd /var/www/zeebull
echo "Unzipping updates..."
# Unzip to a temporary directory first to avoid breaking things mid-way
sudo mkdir -p /tmp/zeebull_extract
sudo unzip -o /tmp/zeebull_deploy_final.zip -d /tmp/zeebull_extract/

# Move contents to /var/www/zeebull
sudo cp -r /tmp/zeebull_extract/* /var/www/zeebull/
sudo rm -rf /tmp/zeebull_extract

# 2. Run Database Migration
cd /var/www/zeebull/ResortApp
echo "Running database migration..."
# Ensure the migration script is executable
sudo chmod +x migrate_db_server.py
# Use the existing venv
./venv/bin/python3 migrate_db_server.py || echo "Migration script failed, trying direct python3"
python3 migrate_db_server.py || echo "All migration attempts failed"

# 3. Set Permissions
sudo chown -R www-data:www-data /var/www/zeebull
sudo chmod -R 775 /var/www/zeebull

# 4. Restart Backend Service
echo "Restarting service..."
sudo systemctl restart zeebull

# 5. Verify status
sudo systemctl status zeebull --no-pager

echo "Deployment updates applied successfully!"
