import psycopg2
import os

# INSTRUCTIONS FOR PRODUCTION:
# 1. Ensure you have backup of your database before running this.
# 2. Update the connection string below with your PRODUCTION credentials.
# 3. This script is "safe" - it checks if tables/columns exist before creating them.

PRODUCTION_DB_URL = "postgresql://postgres:qwerty123@localhost:5432/zeebull"

def run_safe_migration():
    try:
        conn = psycopg2.connect(PRODUCTION_DB_URL)
        cur = conn.cursor()
        
        print("Checking for rate_plans table...")
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'rate_plans');")
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("Creating rate_plans table...")
            cur.execute("""
                CREATE TABLE rate_plans (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    room_type_id INTEGER REFERENCES room_types(id),
                    occupancy INTEGER DEFAULT 2,
                    meal_plan VARCHAR,
                    channel_manager_id VARCHAR,
                    base_price FLOAT DEFAULT 0.0,
                    weekend_price FLOAT,
                    price_offset FLOAT DEFAULT 0.0,
                    branch_id INTEGER REFERENCES branches(id) NOT NULL
                );
                CREATE INDEX ix_rate_plans_id ON rate_plans (id);
                CREATE INDEX ix_rate_plans_branch_id ON rate_plans (branch_id);
            """)
            print("Table rate_plans created.")
        else:
            print("Table rate_plans already exists. Checking for new columns...")
            
            # Check for base_price
            cur.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name='rate_plans' AND column_name='base_price';")
            if not cur.fetchone():
                print("Adding column base_price...")
                cur.execute("ALTER TABLE rate_plans ADD COLUMN base_price FLOAT DEFAULT 0.0;")
                
            # Check for weekend_price
            cur.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name='rate_plans' AND column_name='weekend_price';")
            if not cur.fetchone():
                print("Adding column weekend_price...")
                cur.execute("ALTER TABLE rate_plans ADD COLUMN weekend_price FLOAT;")

            # Check for price_offset
            cur.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name='rate_plans' AND column_name='price_offset';")
            if not cur.fetchone():
                print("Adding column price_offset...")
                cur.execute("ALTER TABLE rate_plans ADD COLUMN price_offset FLOAT DEFAULT 0.0;")

        conn.commit()
        print("\nSUCCESS: Production database is now up to date.")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\nERROR during migration: {e}")
        print("Make sure your production DB is reachable and credentials are correct.")

if __name__ == "__main__":
    run_safe_migration()
