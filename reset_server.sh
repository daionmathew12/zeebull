#!/bin/bash
set -e

echo "Stopping service..."
sudo systemctl stop inventory-resort.service || true

echo "Forcefully terminating database connections..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'zeebulldb' AND pid != pg_backend_pid();" || true

echo "Dropping database zeebulldb..."
sudo -u postgres dropdb --if-exists zeebulldb

echo "Creating database zeebulldb..."
sudo -u postgres createdb -O orchid_user zeebulldb

echo "Removing application directory..."
sudo rm -rf /var/www/zeebull

echo "Cleanup complete."
