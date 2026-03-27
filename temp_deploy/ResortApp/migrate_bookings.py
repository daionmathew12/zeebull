import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Hardcoded for safety
SQLALCHEMY_DATABASE_URL = 'postgresql://orchid_user:admin123@localhost/orchid_resort'

def migrate_bookings():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        print("Migrating bookings table...")
        
        # created_at
        try:
            check = conn.execute(text("SELECT 1 FROM information_schema.columns WHERE table_name='bookings' AND column_name='created_at'")).fetchone()
            if not check:
                print("Adding created_at to bookings...")
                conn.execute(text("ALTER TABLE bookings ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                conn.commit()
                print("Added created_at successfully.")
            else:
                print("created_at already exists in bookings.")
        except Exception as e:
            print(f"Error adding created_at: {e}")

        # status
        try:
            check = conn.execute(text("SELECT 1 FROM information_schema.columns WHERE table_name='bookings' AND column_name='status'")).fetchone()
            if not check:
                print("Adding status to bookings...")
                conn.execute(text("ALTER TABLE bookings ADD COLUMN status VARCHAR DEFAULT 'confirmed'"))
                conn.commit()
                print("Added status successfully.")
            else:
                print("status already exists in bookings.")
        except Exception as e:
            print(f"Error adding status: {e}")

        # check_in / check_out (just in case)
        for col in ['check_in', 'check_out']:
            try:
                check = conn.execute(text(f"SELECT 1 FROM information_schema.columns WHERE table_name='bookings' AND column_name='{col}'")).fetchone()
                if not check:
                    print(f"Adding {col} to bookings...")
                    conn.execute(text(f"ALTER TABLE bookings ADD COLUMN {col} DATE"))
                    conn.commit()
                else:
                    print(f"{col} already exists in bookings.")
            except Exception as e:
                print(f"Error adding {col}: {e}")

        print("Migration complete.")

if __name__ == "__main__":
    migrate_bookings()
