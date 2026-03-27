import os
import sys

sys.path.append('/var/www/inventory/ResortApp')

from sqlalchemy import text
from app.database import SessionLocal

def check_data():
    db = SessionLocal()
    try:
        print("Checking key tables...")
        
        tables = ['branches', 'rooms', 'users', 'food_items']
        for table in tables:
            try:
                res = db.execute(text(f"SELECT count(*) FROM {table}")).scalar()
                print(f"{table} count: {res}")
                if res > 0:
                    rows = db.execute(text(f"SELECT * FROM {table} LIMIT 5")).fetchall()
                    print(f"Sample {table}: {rows}")
            except Exception as e:
                print(f"Error checking {table}: {e}")
                
        # Check database name
        res = db.execute(text("SELECT current_database()")).scalar()
        print(f"Current Database: {res}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
