sudo -u postgres psql orchid_resort -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'food_orders';"
