import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))
from sqlalchemy import text
from app.database import SessionLocal

def check_banners():
    db = SessionLocal()
    try:
        # Check columns of header_banners table
        print("=== header_banners table columns ===")
        # For Postgres
        columns = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'header_banners'")).fetchall()
        for col in columns:
            print(f"Column: {col.column_name}, Type: {col.data_type}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_banners()
