#!/bin/bash
sudo -u postgres psql -c "CREATE DATABASE zeebulldb;" || echo "zeebulldb exists"
sudo -u postgres psql -c "CREATE USER orchid_user WITH PASSWORD 'admin123';" || echo "user exists"
sudo -u postgres psql -c "ALTER DATABASE zeebulldb OWNER TO orchid_user;"
sudo -u postgres psql -c "ALTER USER orchid_user WITH SUPERUSER;"
