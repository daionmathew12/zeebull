#!/bin/bash
set -x

# Setup directory
sudo mkdir -p /var/www/zeebull
sudo chown -R $USER:www-data /var/www/zeebull
chmod -R 775 /var/www/zeebull

# Wipe old content to avoid collisions
rm -rf /var/www/zeebull/*

# Extract zip
unzip -o /tmp/zeebull_deploy_final.zip -d /var/www/zeebull/

# Correct permissions after unzip
sudo chown -R $USER:www-data /var/www/zeebull
sudo chmod -R 775 /var/www/zeebull

# Setup Python
cd /var/www/zeebull/ResortApp
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install gunicorn uvicorn

# REMOVE problematic gunicorn config if it exists
if [ -f "gunicorn.conf.py" ]; then
    mv gunicorn.conf.py gunicorn.conf.py.bak
fi

# Setup Environment
cat <<EOF > .env
DATABASE_URL=postgresql+psycopg2://orchid_user:admin123@localhost/orchid_resort
SECRET_KEY=9a3a9a3a9a3a9a3a9a3a9a3a9a3a9a3a
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
DEBUG=False
EOF

# Database Initialization
./venv/bin/python3 -m alembic upgrade head || echo "Alembic failed, trying manual table creation"
./venv/bin/python3 -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)" || echo "Manual table creation failed"
./venv/bin/python3 seed_roles.py || echo "Seeding roles failed"
./venv/bin/python3 setup_superadmin.py || echo "Setup superadmin failed"

# Setup Service
sudo mv /tmp/zeebull.service /etc/systemd/system/zeebull.service
sudo systemctl daemon-reload
sudo systemctl enable zeebull
sudo systemctl restart zeebull

# Setup Nginx
sudo mv /tmp/nginx_zeebull.conf /etc/nginx/sites-available/teqmates
sudo nginx -t && sudo systemctl reload nginx

echo "Deployment complete!"
