#!/bin/bash

# Configuration
APP_DIR="/var/www/inventory"
REPO_DIR="$HOME/ResortwithGstinventry"
USER="www-data"
GROUP="www-data"

echo "============================================================"
echo "Starting Deployment Process..."
echo "============================================================"

# 1. Update Repository
echo "[1/7] Updating Repository..."
cd $REPO_DIR
# Fetch latest changes (assuming we want to deploy the current branch)
git fetch origin
# You might want to hard reset to match origin if you don't care about local changes
# git reset --hard origin/deployment-inventory
git pull

# 2. Stop Services
echo "[2/7] Stopping Services..."
sudo systemctl stop inventory-resort

# 3. Frontend Build (Admin Dashboard)
echo "[3/7] Building Frontend (Admin Dashboard)..."
cd $REPO_DIR/dasboard
# Install dependencies if package.json changed
if [ -f "package.json" ]; then
    npm install --legacy-peer-deps
fi
# Build
npm run build
# Deploy to webroot
echo "Deploying Frontend to $APP_DIR/html..."
sudo mkdir -p $APP_DIR/html
sudo rm -rf $APP_DIR/html/*
sudo cp -r build/* $APP_DIR/html/

# 3.5. Userend Build (Guest Interface)
echo "[3.5/7] Building Userend (Guest Interface)..."
cd $REPO_DIR/userend
# Install dependencies if package.json changed
if [ -f "package.json" ]; then
    npm install --legacy-peer-deps
fi
# Build
npm run build
# Deploy to webroot
echo "Deploying Userend to $APP_DIR/userend_html..."
sudo mkdir -p $APP_DIR/userend_html
sudo rm -rf $APP_DIR/userend_html/*
sudo cp -r build/* $APP_DIR/userend_html/

# 4. Backend Setup
echo "[4/7] Setting up Backend..."
# Copy new backend files to application directory
cp -r $REPO_DIR/ResortApp/* $APP_DIR/ResortApp/

# Ensure virtual environment exists
if [ ! -d "$APP_DIR/venv" ]; then
    echo "Creating virtual environment..."
    sudo -u $USER python3 -m venv $APP_DIR/venv
fi

# Install dependencies
echo "Installing Python dependencies..."
sudo -u $USER $APP_DIR/venv/bin/pip install --upgrade pip
if [ -f "$APP_DIR/ResortApp/requirements.txt" ]; then
    sudo -u $USER $APP_DIR/venv/bin/pip install -r $APP_DIR/ResortApp/requirements.txt
fi
sudo -u $USER $APP_DIR/venv/bin/pip install gunicorn uvicorn psycopg2-binary alembic

# 5. Permissions & Env
echo "[5/7] Setting Permissions & Env..."

# Create .env if missing (using dummy values to prevent crash if real one is gone)
if [ ! -f "$APP_DIR/ResortApp/.env" ]; then
    echo "Creating dummy .env file..."
    echo "DATABASE_URL=sqlite:///./orchid.db" > $APP_DIR/ResortApp/.env
    echo "SECRET_KEY=dummy-secret" >> $APP_DIR/ResortApp/.env
fi

# Set permissions
sudo chown -R $USER:$GROUP $APP_DIR
sudo chmod -R 755 $APP_DIR
sudo chmod -R 775 $APP_DIR/ResortApp/uploads
sudo chmod -R 775 $APP_DIR/ResortApp/static

# 6. Database Migrations & Seeding
echo "[6/7] Running Database Migrations & Seeding..."
cd $APP_DIR/ResortApp
# Run migrations (stamp head if issues arise, upgrade normally otherwise)
# We use '|| true' to prevent script exit on migration failure, as sometimes manual intervention is needed
sudo -u $USER $APP_DIR/venv/bin/python3 -m alembic upgrade head || echo "Warning: Alembic migration failed, check logs"

# Run Seeding Script if available
if [ -f "seed_accounting_data.py" ]; then
    echo "Running Accounting Seed Script..."
    sudo -u $USER $APP_DIR/venv/bin/python3 seed_accounting_data.py
fi

# 7. Restart Services
echo "[7/7] Restarting Services..."
sudo systemctl start inventory-resort
sudo systemctl status inventory-resort --no-pager

echo "============================================================"
echo "Deployment Completed Successfully!"
echo "============================================================"
