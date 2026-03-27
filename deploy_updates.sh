#!/bin/bash
set -x

# 1. Setup zeebull directory
sudo mkdir -p /var/www/zeebull
sudo chown -R $USER:www-data /var/www/zeebull
chmod -R 775 /var/www/zeebull

# Wipe old content
rm -rf /var/www/zeebull/*

# Extract zeebull app
unzip -o /tmp/zeebull_deploy_final.zip -d /var/www/zeebull/

# Correct permissions
sudo chown -R $USER:www-data /var/www/zeebull
sudo chmod -R 775 /var/www/zeebull

# 2. Setup Landing Page
sudo mkdir -p /var/www/landing
sudo chown -R $USER:www-data /var/www/landing
rm -rf /var/www/landing/*
unzip -o /tmp/landingpage.zip -d /var/www/landing/
sudo chown -R $USER:www-data /var/www/landing
sudo chmod -R 755 /var/www/landing

# 3. Setup Python Backend
cd /var/www/zeebull/ResortApp
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install gunicorn uvicorn

# Setup .env
cat <<EOF > .env
DATABASE_URL=postgresql+psycopg2://orchid_user:admin123@localhost/zeebulldb
SECRET_KEY=9a3a9a3a9a3a9a3a9a3a9a3a9a3a9a3a
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
DEBUG=False
EOF

# Database Initialization
./venv/bin/python3 -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)" || echo "Table creation failed"
./venv/bin/python3 seed_roles.py || echo "Seeding roles failed"
./venv/bin/python3 setup_superadmin.py || echo "Setup superadmin failed"
# Also need the initial data seed (Branch 1)
./venv/bin/python3 seed_initial_data.py || echo "Initial data seeding failed"

# 4. Setup Service
sudo mv /tmp/zeebull.service /etc/systemd/system/zeebull.service
sudo systemctl daemon-reload
sudo systemctl enable zeebull
sudo systemctl restart zeebull

# 5. Setup Nginx
sudo mv /tmp/nginx_zeebull_new.conf /etc/nginx/sites-available/zeebull
sudo ln -sf /etc/nginx/sites-available/zeebull /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo "Deployment to new VM complete!"
