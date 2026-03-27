#!/bin/bash
# COMPREHENSIVE Remote Deployment Script
# Targets /var/www/zeebull and /var/www/landing

# Configuration
HOME_DIR="/home/basilabrahamaby"
APP_DIR="/var/www/zeebull"
LANDING_DIR="/var/www/landing"
NGINX_CONF="/etc/nginx/sites-available/zeebull"

# 1. STOP SERVICE
echo "Stopping zeebull.service..."
sudo systemctl stop zeebull.service || true

# 2. IDENTIFY BACKUP (Using the existing backup from Step 1)
BACKUP_DIR=$(ls -td /var/www/zeebull_backup_* | head -1)
echo "Using backup from $BACKUP_DIR for configuration restoration..."

# 3. CLEAN & EXTRACT
echo "Extracting bundles to $APP_DIR..."
# Backend
sudo mkdir -p $APP_DIR/ResortApp
sudo unzip -o "$HOME_DIR/resortapp_deploy.zip" -d "$APP_DIR/ResortApp" || true

# Dashboard
sudo mkdir -p $APP_DIR/dasboard
sudo unzip -o "$HOME_DIR/dashboard_deploy.zip" -d "$APP_DIR/dasboard" || true

# Userend
sudo mkdir -p $APP_DIR/userend
sudo unzip -o "$HOME_DIR/userend_deploy.zip" -d "$APP_DIR/userend" || true

# Landing
sudo mkdir -p $LANDING_DIR
sudo unzip -o "$HOME_DIR/landingpage.zip" -d "$LANDING_DIR" || true

# 4. RESTORE PERSISTENT FILES
echo "Restoring persistent files from $BACKUP_DIR..."
if [ -d "$BACKUP_DIR" ]; then
    # Restore .env
    if [ -f "$BACKUP_DIR/ResortApp/.env" ]; then
        sudo cp "$BACKUP_DIR/ResortApp/.env" "$APP_DIR/ResortApp/.env"
        echo "Restored .env"
    fi
    # Restore venv (essential for service)
    if [ -d "$BACKUP_DIR/ResortApp/venv" ]; then
        sudo cp -r "$BACKUP_DIR/ResortApp/venv" "$APP_DIR/ResortApp/"
        echo "Restored venv"
    fi
    # Restore uploads
    if [ -d "$BACKUP_DIR/ResortApp/uploads" ]; then
        sudo cp -r "$BACKUP_DIR/ResortApp/uploads" "$APP_DIR/ResortApp/"
        echo "Restored uploads"
    fi
else
    echo "Warning: No backup found to restore configuration from!"
fi

# 5. RECREATE TABLE SCRIPT (Copy it in)
echo "Copying over recreation script..."
sudo cp "$HOME_DIR/recreate_all_tables.py" "$APP_DIR/ResortApp/"

# 6. PERMISSIONS
echo "Fixing permissions..."
sudo chown -R basilabrahamaby:www-data $APP_DIR
sudo chown -R basilabrahamaby:www-data $LANDING_DIR
sudo chmod -R 775 $APP_DIR
sudo chmod -R 775 $LANDING_DIR

# 7. NGINX
echo "Updating Nginx configuration..."
sudo bash -c "cat > $NGINX_CONF" << EOF
server {
    client_max_body_size 50M;
    server_name teqmates.com www.teqmates.com;

    root $LANDING_DIR;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Zeebull Admin Dashboard
    location ^~ /zeebulladmin {
        alias $APP_DIR/dasboard;
        try_files \$uri \$uri/ /zeebulladmin/index.html;
    }

    # Zeebull User Frontend
    location ^~ /zeebull {
        alias $APP_DIR/userend;
        try_files \$uri \$uri/ /zeebull/index.html;
    }

    # Zeebull Backend API
    location ^~ /zeebullapi/ {
        proxy_pass http://127.0.0.1:8012/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
    }

    # Zeebull Static Files
    location ^~ /zeebullfiles/ {
        alias $APP_DIR/ResortApp/;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/teqmates.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/teqmates.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if (\$host = www.teqmates.com) {
        return 301 https://\$host\$request_uri;
    } # managed by Certbot

    if (\$host = teqmates.com) {
        return 301 https://\$host\$request_uri;
    } # managed by Certbot

    listen 80;
    server_name teqmates.com www.teqmates.com;
    return 404; # managed by Certbot
}
EOF

# 8. START SERVICES
echo "Restarting services..."
sudo systemctl daemon-reload
sudo systemctl start zeebull.service
sudo systemctl restart nginx

echo "Deployment complete."
