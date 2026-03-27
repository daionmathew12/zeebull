import sys
import os

# Add ResortApp to path
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))

from app.database import SessionLocal
from sqlalchemy import text

def check_structure():
    db = SessionLocal()
    try:
        # Check services table
        print("Services table branch_id nullable check:")
        # For Postgres
        res = db.execute(text("SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = 'services' AND column_name = 'branch_id'")).fetchone()
        print(f"Postgres result: {res}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_structure()
