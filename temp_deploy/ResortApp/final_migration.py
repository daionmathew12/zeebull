from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

def migrate():
    # Load .env explicitly
    env_path = Path("/var/www/inventory/ResortApp/.env")
    load_dotenv(dotenv_path=env_path)
    
    db_url = os.getenv("DATABASE_URL")
    print(f"Migrating database: {db_url[:40]}...")
    
    engine = create_engine(db_url)
    
    with engine.begin() as conn: # engine.begin() handles transaction commit/rollback
        print("Checking package_bookings structure manually...")
        
        # Check if total_amount exists
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'package_bookings' AND column_name = 'total_amount'"))
        if not result.fetchone():
            print("Adding total_amount column...")
            conn.execute(text("ALTER TABLE package_bookings ADD COLUMN total_amount DOUBLE PRECISION DEFAULT 0.0"))
            print("Successfully added total_amount")
        else:
            print("total_amount already exists")
            
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
