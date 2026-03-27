#!/bin/bash
set -e

echo "Creating zeebulldb..."
sudo -u postgres psql -c "CREATE DATABASE zeebulldb OWNER orchid_user;" || echo "Database might already exist"

echo "Updating .env..."
ENV_FILE="/var/www/zeebull/ResortApp/.env"
sudo sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg2://orchid_user:admin123@localhost/zeebulldb|' $ENV_FILE

echo "Checking .env content:"
sudo cat $ENV_FILE

echo "Initializing database tables..."
cd /var/www/zeebull/ResortApp
./venv/bin/python3 -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"

echo "Seeding initial data..."
./venv/bin/python3 seed_initial_data.py

echo "Verifying service restart..."
sudo systemctl restart zeebull

echo "Database migration to zeebulldb complete!"
