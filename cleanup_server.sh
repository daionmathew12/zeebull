#!/bin/bash
set -ex
sudo systemctl stop inventory-resort.service || true
sudo systemctl stop nginx || true
sudo rm -rf /var/www/zeebull/*
sudo mkdir -p /var/www/zeebull/ResortApp
sudo chown -R $USER:$USER /var/www/zeebull

# DB Reset
# Kill connections
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'zeebulldb';" || true
# Drop/Create
sudo -u postgres dropdb --if-exists zeebulldb
sudo -u postgres createdb zeebulldb
# User setup
sudo -u postgres psql -c "DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'zeebull') THEN
        CREATE USER zeebull WITH PASSWORD 'zeebullpass';
    END IF;
END \$\$;"
sudo -u postgres psql -c "ALTER DATABASE zeebulldb OWNER TO zeebull; GRANT ALL PRIVILEGES ON DATABASE zeebulldb TO zeebull;"
