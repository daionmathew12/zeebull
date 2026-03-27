from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def fix_schema():
    with engine.connect() as conn:
        print("Starting schema fix...")
        
        # 1. Create branches table if not exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS branches (
                id SERIAL PRIMARY KEY,
                name VARCHAR,
                code VARCHAR UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                address TEXT,
                phone VARCHAR,
                email VARCHAR,
                gst_number VARCHAR,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("Ensured 'branches' table exists.")

        # 2. Add columns to users table
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN branch_id INTEGER REFERENCES branches(id)"))
            print("Added branch_id to users.")
        except Exception as e:
            print(f"branch_id might already exist in users: {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN DEFAULT FALSE"))
            print("Added is_superadmin to users.")
        except Exception as e:
            print(f"is_superadmin might already exist in users: {e}")

        # 3. Add branch_id to other core tables if missing
        tables = ["rooms", "bookings", "expenses", "employees", "food_orders", "assigned_services", "checkouts"]
        for table in tables:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN branch_id INTEGER REFERENCES branches(id)"))
                print(f"Added branch_id to {table}.")
            except Exception as e:
                print(f"branch_id might already exist in {table}: {e}")

        conn.commit()
        print("Schema fix complete.")

if __name__ == "__main__":
    fix_schema()
