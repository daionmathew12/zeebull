import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Hardcoded for safety if app.database fails
SQLALCHEMY_DATABASE_URL = 'postgresql://orchid_user:admin123@localhost/orchid_resort'

def migrate_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        print("Starting Repair Migration...")

        def add_col(table, col, defn):
            try:
                check = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='{col}'")).fetchone()
                if not check:
                    print(f"Adding {col} to {table}...")
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {defn}"))
                    conn.commit()
                else:
                    print(f"Col {col} in {table} already exists.")
            except Exception as e:
                print(f"Error on {table}.{col}: {e}")

        # ROOMS
        feats = ['air_conditioning', 'wifi', 'bathroom', 'living_area', 'terrace', 'parking', 'kitchen', 'family_room', 'bbq', 'garden', 'dining', 'breakfast']
        for f in feats:
            add_col('rooms', f, 'BOOLEAN DEFAULT FALSE')
        
        # PACKAGES
        add_col('packages', 'booking_type', 'VARCHAR(50) DEFAULT \'room_type\'')
        add_col('packages', 'room_types', 'TEXT')
        add_col('packages', 'theme', 'VARCHAR')
        add_col('packages', 'default_adults', 'INTEGER DEFAULT 2')
        add_col('packages', 'default_children', 'INTEGER DEFAULT 0')
        add_col('packages', 'max_stay_days', 'INTEGER')
        add_col('packages', 'food_included', 'VARCHAR')
        add_col('packages', 'food_timing', 'TEXT')
        add_col('packages', 'complimentary', 'TEXT')
        add_col('packages', 'status', 'VARCHAR DEFAULT \'active\'')
        add_col('packages', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

        # PACKAGE_BOOKINGS
        add_col('package_bookings', 'check_in', 'DATE')
        add_col('package_bookings', 'check_out', 'DATE')
        add_col('package_bookings', 'checked_in_at', 'TIMESTAMP')
        add_col('package_bookings', 'adults', 'INTEGER DEFAULT 2')
        add_col('package_bookings', 'children', 'INTEGER DEFAULT 0')
        add_col('package_bookings', 'advance_deposit', 'DOUBLE PRECISION DEFAULT 0')
        add_col('package_bookings', 'total_amount', 'DOUBLE PRECISION DEFAULT 0')
        add_col('package_bookings', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

        # SERVICE_REQUESTS
        add_col('service_requests', 'billing_status', 'VARCHAR')
        add_col('service_requests', 'started_at', 'TIMESTAMP')

        # ASSIGNED_SERVICES
        add_col('assigned_services', 'started_at', 'TIMESTAMP')
        add_col('assigned_services', 'completed_at', 'TIMESTAMP')
        add_col('assigned_services', 'override_charges', 'DOUBLE PRECISION')
        add_col('assigned_services', 'billing_status', 'VARCHAR')

        print("Migration Repair Finished.")

if __name__ == "__main__":
    migrate_database()
