#!/bin/bash
set -x

echo "Recreating database for Zeebull..."
# Terminate any existing connections to the database to allow dropping it (if it exists)
sudo -u postgres psql -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'zeebull_db' AND pid <> pg_backend_pid();" || true

# Drop the database and recreate it
sudo -u postgres psql -c "DROP DATABASE IF EXISTS zeebull_db;"
sudo -u postgres psql -c "CREATE DATABASE zeebull_db OWNER orchid_user;"

echo "Updating environment configuration..."
cat <<EOF > /var/www/zeebull/ResortApp/.env
DATABASE_URL=postgresql+psycopg2://orchid_user:admin123@localhost/zeebull_db
SECRET_KEY=9a3a9a3a9a3a9a3a9a3a9a3a9a3a9a3a
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
DEBUG=False
EOF

echo "Restarting Zeebull to initialize the new schema..."
sudo systemctl restart zeebull

echo "Finished database setup!"
