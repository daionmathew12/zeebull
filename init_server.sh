#!/bin/bash
set -e

echo "Starting Server Initialization..."

# Update and Install Dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx git curl build-essential unzip certbot python3-certbot-nginx

# Setup Postgres
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create Database and User if they don't exist
# Check if user exists
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='orchid_user'" | grep -q 1; then
    sudo -u postgres psql -c "CREATE USER orchid_user WITH PASSWORD 'admin123';"
    sudo -u postgres psql -c "ALTER USER orchid_user WITH SUPERUSER;"
fi

# Check if database exists
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw zeebulldb; then
    sudo -u postgres psql -c "CREATE DATABASE zeebulldb OWNER orchid_user;"
fi

# Install Node.js
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# Create directory structure
sudo mkdir -p /var/www/zeebull
sudo chown -R $USER:www-data /var/www/zeebull
sudo chmod -R 775 /var/www/zeebull

# Prepare Nginx
sudo rm -f /etc/nginx/sites-enabled/default

echo "Server Initialization Complete!"
