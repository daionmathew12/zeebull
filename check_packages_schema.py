import sys
import os

# Add ResortApp to path
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))

from app.database import SessionLocal
from sqlalchemy import text

def check_structure():
    db = SessionLocal()
    try:
        # Check packages table
        print("Packages table columns:")
        res = db.execute(text("SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = 'packages'")).fetchall()
        for r in res:
            print(f"Col: {r[0]}, Nullable: {r[1]}, Type: {r[2]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_structure()
