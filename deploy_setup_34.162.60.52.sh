#!/bin/bash
# Zeebull Hospitality - Production Deployment Setup (v4)
# Target: 34.162.60.52
# Date: 2026-04-08

set -e

APP_DIR="/var/www/zeebull"
BACKEND_DIR="$APP_DIR/ResortApp"
DASHBOARD_DIR="$APP_DIR/dasboard"
USEREND_DIR="$APP_DIR/userend"
USER="basilabrahamaby"
DB_NAME="zeebuldb"
DB_USER="postgres"
DB_PASS="qwerty123"

echo "========================================"
echo "Starting Zeebull Hospitality Deployment"
echo "========================================"

# 1. Prepare Directories
sudo mkdir -p $APP_DIR
sudo mkdir -p $BACKEND_DIR
sudo mkdir -p $DASHBOARD_DIR/build
sudo mkdir -p $USEREND_DIR/build
sudo chown -R $USER:www-data $APP_DIR

# 2. Extract Bundles
echo "Extracting bundles..."
if [ -f /tmp/zeebull_backend.zip ]; then
    # Targeted deletion: Remove everything EXCEPT persistent folders
    find $BACKEND_DIR -mindepth 1 -maxdepth 1 ! -name 'uploads' ! -name 'venv' -exec rm -rf {} +
    unzip -o /tmp/zeebull_backend.zip -d $BACKEND_DIR
    echo "Backend extracted."
fi
if [ -f /tmp/zeebull_admin.zip ]; then
    sudo rm -rf $DASHBOARD_DIR/build/*
    unzip -o /tmp/zeebull_admin.zip -d $DASHBOARD_DIR/build
    echo "Admin Dashboard extracted."
fi
if [ -f /tmp/zeebull_userend.zip ]; then
    sudo rm -rf $USEREND_DIR/build/*
    unzip -o /tmp/zeebull_userend.zip -d $USEREND_DIR/build
    echo "User End extracted."
fi

# 3. Environment Variable Setup (.env)
echo "Configuring .env..."
cat <<EOF > $BACKEND_DIR/.env
DATABASE_URL=postgresql+psycopg2://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
PORT=8011
SECRET_KEY=zeebull-production-secret-9a3a9a3a
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Aiosell Channel Manager
AIOSELL_ACTIVE=true
AIOSELL_HOTEL_CODE=a0e3cff078
AIOSELL_PARTNER_ID=teqmates-hospitality
AIOSELL_API_URL=https://live.aiosell.com/api/v2/cm/update
AIOSELL_USERNAME=teqmates-hospitality
AIOSELL_PASSWORD=1zdv6udu
AIOSELL_WEBHOOK_USERNAME=teqmates-hospitality
AIOSELL_WEBHOOK_PASSWORD=1zdv6udu
EOF

# 4. Database Setup
echo "Ensuring database exists..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || sudo -u postgres psql -c "CREATE DATABASE $DB_NAME"
sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';" || true

# 5. Backend dependencies (venv)
echo "Setting up Python virtual environment..."
cd $BACKEND_DIR
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p uploads

# 6. Database Seeding
echo "Checking and seeding database..."
cat <<EOF > seed_deployment_data.py
from app.database import SessionLocal, engine, Base
from app.models.user import User, Role
from app.models.settings import SystemSetting
from app.utils.auth import get_password_hash
import json

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 1. Seed Admin Role
admin_role = db.query(Role).filter(Role.name == 'admin').first()
if not admin_role:
    print("Creating admin role...")
    admin_role = Role(
        name='admin',
        permissions=json.dumps(["all"])
    )
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)

# 2. Seed Admin User
admin = db.query(User).filter(User.email == 'admin@orchid.com').first()
if not admin:
    print("Seeding admin user...")
    admin = User(
        email='admin@orchid.com',
        hashed_password=get_password_hash('admin123'),
        name='Zeebull Administrator',
        role_id=admin_role.id,
        is_active=True,
        is_superadmin=True
    )
    db.add(admin)
    db.commit()
    print("Admin user created successfully.")

# 3. Seed System Settings
resort_name = db.query(SystemSetting).filter(SystemSetting.key == 'resort_name').first()
if not resort_name:
    print("Seeding default resort details...")
    settings = [
        SystemSetting(key='resort_name', value='Zeebull Hospitality'),
        SystemSetting(key='resort_address', value='Authorized Client Location'),
        SystemSetting(key='currency', value='INR'),
        SystemSetting(key='tax_rate', value='18')
    ]
    db.add_all(settings)
    db.commit()

db.close()
EOF
python seed_deployment_data.py

# 7. Systemd Service Creation
echo "Creating systemd service..."
sudo bash -c "cat <<EOF > /etc/systemd/system/zeebull.service
[Unit]
Description=Zeebull Resort Management API
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$BACKEND_DIR
Environment=\"PATH=$BACKEND_DIR/venv/bin\"
ExecStart=$BACKEND_DIR/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8011
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

# 8. Final Permissions & Service Management
echo "Applying permissions and restarting services..."
sudo chown -R $USER:www-data $APP_DIR
sudo chmod -R 775 $BACKEND_DIR/uploads

sudo systemctl daemon-reload
sudo systemctl enable zeebull
sudo systemctl restart zeebull
sudo systemctl restart nginx

# 9. Health Check Verification
echo "Verifying health..."
sleep 8
curl -s http://127.0.0.1:8011/health || (echo "ERROR: Backend health check failed!" && exit 1)

echo "========================================"
echo "Deployment Complete!"
echo "URL: http://34.162.60.52/"
echo "Admin: http://34.162.60.52/zeebulladmin"
echo "Creds: admin@orchid.com / admin123"
echo "========================================"
