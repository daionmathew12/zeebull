from sqlalchemy import create_engine, text
import os

db_url = "postgresql+psycopg2://orchid_user:admin123@localhost/orchid_resort"
engine = create_engine(db_url)

sql_commands = [
    "ALTER TABLE employees ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE leaves ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE attendances ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE working_logs ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE inventories ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE inventory_items ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE food_orders ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    "ALTER TABLE bookings ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id);",
    
    "UPDATE employees SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE leaves SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE attendances SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE working_logs SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE expenses SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE inventories SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE inventory_items SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE service_requests SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE food_orders SET branch_id = 1 WHERE branch_id IS NULL;",
    "UPDATE bookings SET branch_id = 1 WHERE branch_id IS NULL;"
]

with engine.connect() as conn:
    for cmd in sql_commands:
        try:
            print(f"Executing: {cmd}")
            conn.execute(text(cmd))
            conn.commit()
            print("Success")
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()

print("Schema fix complete.")
