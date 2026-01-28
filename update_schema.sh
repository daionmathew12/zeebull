sudo -u postgres psql orchid_resort -c "ALTER TABLE food_orders ADD COLUMN created_by_id INTEGER REFERENCES employees(id);"
sudo -u postgres psql orchid_resort -c "ALTER TABLE food_orders ADD COLUMN prepared_by_id INTEGER REFERENCES employees(id);"
