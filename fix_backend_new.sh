#!/bin/bash
set -x
cd /var/www/zeebull/ResortApp

# Ensure DB User and DB exist (just in case)
sudo -u postgres psql -c "CREATE DATABASE zeebulldb;" || echo "exists"
sudo -u postgres psql -c "CREATE USER orchid_user WITH PASSWORD 'admin123';" || echo "exists"
sudo -u postgres psql -c "ALTER DATABASE zeebulldb OWNER TO orchid_user;"
sudo -u postgres psql -c "ALTER USER orchid_user WITH SUPERUSER;"

# Re-run initialization
./venv/bin/python3 -c "from app.database import Base, engine; from app.models import *; Base.metadata.create_all(bind=engine)"
./venv/bin/python3 seed_roles.py
./venv/bin/python3 setup_superadmin.py
./venv/bin/python3 seed_initial_data.py

# Restart service
sudo systemctl daemon-reload
sudo systemctl enable zeebull
sudo systemctl restart zeebull

# Check service
sudo systemctl status zeebull --no-pager
