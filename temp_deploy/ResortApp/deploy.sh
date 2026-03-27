#!/bin/bash

# TeqMates Resort Management System - Comprehensive Deployment Script
# This script sets up the complete application on a fresh Ubuntu/Debian server
# with package verification and error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="teqmates.com"
APP_DIR="/var/www/resort"
APP_USER="www-data"
DB_NAME="resort_db"
DB_USER="resort_user"
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
NODE_VERSION="18"

# Log file
LOG_FILE="/var/log/resort_deployment.log"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}     TeqMates Resort Management System - Deployment Script     ${NC}"
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}Domain: ${YELLOW}$DOMAIN${NC}"
echo -e "${BLUE}App Directory: ${YELLOW}$APP_DIR${NC}"
echo -e "${BLUE}Log File: ${YELLOW}$LOG_FILE${NC}"
echo ""

# Function to print status with timestamp
print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" >> $LOG_FILE
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> $LOG_FILE
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> $LOG_FILE
}

print_section() {
    echo ""
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE} $1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if service is running
service_running() {
    systemctl is-active --quiet "$1"
}

# Function to install package if not exists
install_if_missing() {
    if ! dpkg -l | grep -q "^ii  $1 "; then
        print_status "Installing $1..."
        apt-get install -y "$1" || {
            print_error "Failed to install $1"
            exit 1
        }
    else
        print_status "$1 is already installed"
    fi
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Create log file
mkdir -p /var/log
touch $LOG_FILE

print_section "SYSTEM PREPARATION"

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

print_section "INSTALLING SYSTEM DEPENDENCIES"

# Install basic dependencies
print_status "Installing basic system packages..."
apt install -y software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install required packages with individual checks
PACKAGES=(
    "curl"
    "wget"
    "git"
    "unzip"
    "build-essential"
    "libpq-dev"
    "libffi-dev"
    "libssl-dev"
    "python3"
    "python3-pip"
    "python3-venv"
    "python3-dev"
    "postgresql"
    "postgresql-contrib"
    "redis-server"
    "nginx"
    "supervisor"
    "ufw"
    "fail2ban"
    "htop"
    "tree"
    "vim"
    "certbot"
    "python3-certbot-nginx"
)

for package in "${PACKAGES[@]}"; do
    install_if_missing "$package"
done

print_section "INSTALLING NODE.JS"

# Install Node.js
if ! command_exists node || [ "$(node --version | cut -d'.' -f1 | sed 's/v//')" -lt "$NODE_VERSION" ]; then
    print_status "Installing Node.js $NODE_VERSION..."
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt-get install -y nodejs
else
    print_status "Node.js is already installed ($(node --version))"
fi

# Install Yarn (optional but recommended)
if ! command_exists yarn; then
    print_status "Installing Yarn package manager..."
    npm install -g yarn
fi

print_section "CONFIGURING POSTGRESQL"

# Start PostgreSQL if not running
if ! service_running postgresql; then
    print_status "Starting PostgreSQL..."
    systemctl start postgresql
    systemctl enable postgresql
fi

# Configure PostgreSQL
print_status "Setting up PostgreSQL database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" || true
sudo -u postgres createuser -s "$DB_USER" || true
sudo -u postgres createdb "$DB_NAME" || true
sudo -u postgres psql -c "ALTER USER $DB_USER PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

print_section "CONFIGURING REDIS"

# Start Redis if not running
if ! service_running redis-server; then
    print_status "Starting Redis..."
    systemctl start redis-server
    systemctl enable redis-server
fi

# Configure Redis
print_status "Configuring Redis..."
sed -i 's/# maxmemory <bytes>/maxmemory 128mb/' /etc/redis/redis.conf
sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
systemctl restart redis-server

print_section "SETTING UP APPLICATION DIRECTORIES"

# Create application directories
print_status "Creating application directories..."
mkdir -p "$APP_DIR"
mkdir -p /var/log/resort
mkdir -p /var/run/resort
mkdir -p /var/backups/resort

# Check if application files exist in current directory
if [ ! -d "Resort_first" ]; then
    print_error "Resort_first directory not found in current location!"
    print_error "Please ensure you're running this script from the correct directory"
    print_error "or upload your application files first."
    exit 1
fi

print_status "Copying application files..."
cp -r Resort_first "$APP_DIR/"

print_section "SETTING UP PYTHON ENVIRONMENT"

# Create Python virtual environment
print_status "Creating Python virtual environment..."
cd "$APP_DIR/Resort_first/ResortApp"
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python requirements
print_status "Installing Python dependencies..."
if [ -f "requirements_production.txt" ]; then
    pip install -r requirements_production.txt
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_warning "No requirements file found. Installing basic FastAPI dependencies..."
    pip install fastapi uvicorn gunicorn sqlalchemy psycopg2-binary bcrypt passlib python-jose python-multipart pydantic python-dotenv alembic
fi

print_section "BUILDING FRONTEND APPLICATIONS"

# Build Admin Dashboard
print_status "Building Admin Dashboard (React)..."
cd "$APP_DIR/Resort_first/dasboard"
if [ -f "package.json" ]; then
    npm install --legacy-peer-deps

    # Check for build script
    if npm run-script --silent 2>/dev/null | grep -q "build"; then
        npm run build
    else
        print_warning "No build script found in dasboard package.json"
    fi
else
    print_warning "No package.json found in dasboard directory"
fi

# Build User End Application
print_status "Building User Interface (React)..."
if [ -d "$APP_DIR/Resort_first/userend/userend" ]; then
    cd "$APP_DIR/Resort_first/userend/userend"
elif [ -d "$APP_DIR/Resort_first/userend" ]; then
    cd "$APP_DIR/Resort_first/userend"
else
    print_warning "User end directory not found"
fi

if [ -f "package.json" ]; then
    npm install --legacy-peer-deps

    # Check for build script
    if npm run-script --silent 2>/dev/null | grep -q "build"; then
        npm run build
    else
        print_warning "No build script found in userend package.json"
    fi
else
    print_warning "No package.json found in userend directory"
fi

print_section "CONFIGURING APPLICATION"

# Create production environment file
print_status "Creating production environment configuration..."
cd "$APP_DIR/Resort_first/ResortApp"

cat > .env.production << EOF
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=False

# Database Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Security Configuration
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Domain Configuration
DOMAIN=$DOMAIN
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,$(curl -s ifconfig.me)

# CORS Configuration
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN

# File Upload Configuration
MAX_FILE_SIZE=10485760
UPLOAD_FOLDER=uploads
STATIC_FOLDER=static

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/resort/app.log

# SSL Configuration
SSL_ENABLED=True
SSL_CERT_PATH=/etc/letsencrypt/live/$DOMAIN/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/$DOMAIN/privkey.pem

# Frontend Paths
LANDING_PAGE_PATH=../landingpage
DASHBOARD_PATH=../dasboard/build
USEREND_PATH=../userend/userend/build

# SMTP Email Configuration (Required for booking confirmation emails)
# IMPORTANT: Update these values with your actual SMTP credentials
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM_EMAIL=noreply@elysianretreat.com
SMTP_FROM_NAME=Elysian Retreat
SMTP_USE_TLS=true
EOF

# Copy environment file to .env
cp .env.production .env

print_status "SMTP Configuration Note:"
print_warning "Please update SMTP settings in .env.production with your actual email credentials"
print_warning "See SMTP_SETUP_GUIDE.md for detailed instructions"

print_section "INITIALIZING DATABASE"

# Run database migrations
print_status "Setting up database tables..."
source venv/bin/activate
python -c "
try:
    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    print('Database tables created successfully')
except Exception as e:
    print(f'Database setup error: {e}')
    exit(1)
"

print_section "CONFIGURING SYSTEMD SERVICE"

# Create systemd service file if it doesn't exist
if [ ! -f "resort.service" ]; then
    print_status "Creating systemd service file..."
    cat > resort.service << EOF
[Unit]
Description=Resort Management System - TeqMates
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/Resort_first/ResortApp
Environment=PATH=$APP_DIR/Resort_first/ResortApp/venv/bin
Environment=PYTHONPATH=$APP_DIR/Resort_first/ResortApp
EnvironmentFile=$APP_DIR/Resort_first/ResortApp/.env.production
ExecStart=$APP_DIR/Resort_first/ResortApp/venv/bin/gunicorn main:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$APP_DIR/Resort_first/ResortApp/uploads
ReadWritePaths=$APP_DIR/Resort_first/ResortApp/static
ReadWritePaths=/var/log/resort
ReadWritePaths=/var/run/resort

# Resource limits
LimitNOFILE=65536
LimitNPROC=32768

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=resort-management

[Install]
WantedBy=multi-user.target
EOF
fi

# Install systemd service
print_status "Installing systemd service..."
cp resort.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable resort.service

print_section "CONFIGURING NGINX"

# Create Nginx configuration if it doesn't exist
if [ ! -f "nginx.conf" ]; then
    print_status "Creating Nginx configuration..."
    cat > nginx.conf << EOF
# Nginx configuration for TeqMates Resort Management System
# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=general:10m rate=1r/s;

# Upstream backend server
upstream resort_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://www.$DOMAIN\$request_uri;
}

# Main server block - HTTPS
server {
    listen 443 ssl http2;
    server_name www.$DOMAIN $DOMAIN;

    # SSL Configuration (will be configured by certbot)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    client_max_body_size 50M;
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;

    root $APP_DIR/Resort_first;

    # Landing Page - Root path (/)
    location = / {
        try_files /landingpage/index.html @backend;
    }

    # Landing page static assets
    location /assets/ {
        alias $APP_DIR/Resort_first/landingpage/assets/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Admin Dashboard - /admin routes
    location /admin {
        alias $APP_DIR/Resort_first/dasboard/build;
        try_files \$uri \$uri/ /admin/index.html;
    }

    # Admin dashboard static files
    location /admin/static/ {
        alias $APP_DIR/Resort_first/dasboard/build/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # User/Resort interface - /resort routes
    location /resort {
        alias $APP_DIR/Resort_first/userend/userend/build;
        try_files \$uri \$uri/ /resort/index.html;
    }

    # User interface static files
    location /resort/static/ {
        alias $APP_DIR/Resort_first/userend/userend/build/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API routes - All API calls
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://resort_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://resort_backend;
        proxy_set_header Host \$host;
        access_log off;
    }

    # Uploads directory
    location /uploads/ {
        alias $APP_DIR/Resort_first/ResortApp/uploads/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Static files
    location /static/ {
        alias $APP_DIR/Resort_first/ResortApp/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Documentation
    location /docs {
        proxy_pass http://resort_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Security - Block access to sensitive files
    location ~ /\\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~* \\.(env|ini|conf|yml|yaml)\$ {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Backend fallback
    location @backend {
        proxy_pass http://resort_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    access_log /var/log/nginx/resort_access.log;
    error_log /var/log/nginx/resort_error.log;
}
EOF
fi

# Install Nginx configuration
print_status "Installing Nginx configuration..."
cp nginx.conf /etc/nginx/sites-available/resort
ln -sf /etc/nginx/sites-available/resort /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t || {
    print_error "Nginx configuration test failed"
    exit 1
}

print_section "SETTING UP FILE PERMISSIONS"

# Set proper file permissions
print_status "Setting file permissions..."
chown -R $APP_USER:$APP_USER "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod -R 777 "$APP_DIR/Resort_first/ResortApp/uploads" 2>/dev/null || mkdir -p "$APP_DIR/Resort_first/ResortApp/uploads" && chmod -R 777 "$APP_DIR/Resort_first/ResortApp/uploads"
chmod -R 755 "$APP_DIR/Resort_first/ResortApp/static" 2>/dev/null || mkdir -p "$APP_DIR/Resort_first/ResortApp/static" && chmod -R 755 "$APP_DIR/Resort_first/ResortApp/static"
chown -R $APP_USER:$APP_USER /var/log/resort
chown -R $APP_USER:$APP_USER /var/run/resort

print_section "CONFIGURING FIREWALL"

# Setup firewall
print_status "Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 80
ufw allow 443

print_section "STARTING SERVICES"

# Start and enable services
print_status "Starting services..."
systemctl start redis-server
systemctl enable redis-server
systemctl start postgresql
systemctl enable postgresql
systemctl start resort.service
systemctl restart nginx

print_section "SETTING UP SSL CERTIFICATE"

# Setup SSL with Let's Encrypt
print_status "Setting up SSL certificate..."
if certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" --redirect; then
    print_status "SSL certificate installed successfully"
else
    print_warning "SSL setup failed. You may need to configure it manually later."
    print_warning "Run: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

print_section "SETTING UP MONITORING AND MAINTENANCE"

# Create backup script
print_status "Setting up backup script..."
cat > /usr/local/bin/backup-resort.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/resort"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="resort_db"
DB_USER="resort_user"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Files backup
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /var/www/resort/Resort_first/ResortApp/uploads 2>/dev/null || true

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /usr/local/bin/backup-resort.sh

# Setup cron for backups
print_status "Setting up automated backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-resort.sh >> /var/log/resort/backup.log 2>&1") | crontab -

# Create health check script
print_status "Setting up health monitoring..."
cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
LOG_FILE="/var/log/resort/health.log"

if curl -f -s $HEALTH_URL > /dev/null 2>&1; then
    echo "$(date): Health check passed" >> $LOG_FILE
else
    echo "$(date): Health check failed - restarting service" >> $LOG_FILE
    systemctl restart resort.service
fi
EOF

chmod +x /usr/local/bin/health-check.sh

# Setup health check cron (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/health-check.sh") | crontab -

# Create log rotation
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/resort << EOF
/var/log/resort/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload resort.service > /dev/null 2>&1 || true
    endscript
}
EOF

print_section "DEPLOYMENT VERIFICATION"

# Wait for services to start
print_status "Waiting for services to initialize..."
sleep 10

# Check service statuses
print_status "Checking service statuses..."
services=("postgresql" "redis-server" "nginx" "resort.service")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        print_status "$service is running ✓"
    else
        print_error "$service is not running ✗"
    fi
done

print_section "DEPLOYMENT COMPLETED"

# Display deployment summary
echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}               DEPLOYMENT COMPLETED SUCCESSFULLY!              ${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo -e "${CYAN}🌐 URLs:${NC}"
echo -e "  Landing Page:     ${YELLOW}https://www.$DOMAIN/${NC}"
echo -e "  Admin Dashboard:  ${YELLOW}https://www.$DOMAIN/admin${NC}"
echo -e "  User Interface:   ${YELLOW}https://www.$DOMAIN/resort${NC}"
echo -e "  API Docs:         ${YELLOW}https://www.$DOMAIN/docs${NC}"
echo -e "  Health Check:     ${YELLOW}https://www.$DOMAIN/health${NC}"
echo ""
echo -e "${CYAN}🗄️  Database:${NC}"
echo -e "  Host:             ${YELLOW}localhost${NC}"
echo -e "  Database:         ${YELLOW}$DB_NAME${NC}"
echo -e "  User:             ${YELLOW}$DB_USER${NC}"
echo -e "  Password:         ${YELLOW}$DB_PASSWORD${NC}"
echo ""
echo -e "${CYAN}📂 Application:${NC}"
echo -e "  Directory:        ${YELLOW}$APP_DIR${NC}"
echo -e "  User:             ${YELLOW}$APP_USER${NC}"
echo -e "  Logs:             ${YELLOW}/var/log/resort/${NC}"
echo -e "  Service:          ${YELLOW}resort.service${NC}"
echo ""
echo -e "${CYAN}🔧 Service Management:${NC}"
echo -e "  Start:            ${YELLOW}systemctl start resort.service${NC}"
echo -e "  Stop:             ${YELLOW}systemctl stop resort.service${NC}"
echo -e "  Restart:          ${YELLOW}systemctl restart resort.service${NC}"
echo -e "  Status:           ${YELLOW}systemctl status resort.service${NC}"
echo -e "  Logs:             ${YELLOW}journalctl -u resort.service -f${NC}"
echo ""
echo -e "${CYAN}🔒 Security:${NC}"
echo -e "  SSL Certificate:  ${YELLOW}Let's Encrypt (auto-renewal enabled)${NC}"
echo -e "  Firewall:         ${YELLOW}UFW enabled${NC}"
echo -e "  Backups:          ${YELLOW}Daily at 2:00 AM${NC}"
echo -e "  Health Checks:    ${YELLOW}Every 5 minutes${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT NOTES:${NC}"
echo -e "1. ${RED}SAVE THE DATABASE PASSWORD:${NC} $DB_PASSWORD"
echo -e "2. Create your first admin user via API"
echo -e "3. Test all URLs to ensure they're working"
echo -e "4. Configure email settings if needed"
echo -e "5. Monitor logs for any issues"
echo ""
echo -e "${CYAN}📋 Next Steps:${NC}"
echo -e "1. Create admin user:"
echo -e "   ${YELLOW}curl -X POST \"https://www.$DOMAIN/api/users/setup-admin\" \\${NC}"
echo -e "   ${YELLOW}     -H \"Content-Type: application/json\" \\${NC}"
echo -e "   ${YELLOW}     -d '{\"name\": \"Admin\", \"email\": \"admin@$DOMAIN\", \"password\": \"your_password\", \"phone\": \"+1234567890\"}'${NC}"
echo ""
echo -e "2. Test all functionality"
echo -e "3. Set up monitoring alerts"
echo -e "4. Configure email services"
echo ""
echo -e "${GREEN}🎉 Your Resort Management System is now live!${NC}"
echo ""

# Save credentials to file
cat > /root/resort_credentials.txt << EOF
TeqMates Resort Management System - Deployment Credentials
=========================================================

Domain: $DOMAIN
Deployment Date: $(date)

Database:
  Host: localhost
  Database: $DB_NAME
  User: $DB_USER
  Password: $DB_PASSWORD

Application:
  Directory: $APP_DIR
  Service: resort.service
  User: $APP_USER

URLs:
  Landing: https://www.$DOMAIN/
  Admin: https://www.$DOMAIN/admin
  User: https://www.$DOMAIN/resort
  API: https://www.$DOMAIN/docs

Logs: /var/log/resort/
Backups: /var/backups/resort/
EOF

print_status "Deployment completed successfully!"
print_status "Credentials saved to: /root/resort_credentials.txt"
print_status "Log file available at: $LOG_FILE"

echo ""
echo -e "${GREEN}Deployment script finished! 🚀${NC}"
