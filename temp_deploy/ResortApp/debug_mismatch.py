import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal, SQLALCHEMY_DATABASE_URL
from app.models.room import Room
from sqlalchemy import func, text

def debug():
    db = SessionLocal()
    try:
        print(f"URL: {SQLALCHEMY_DATABASE_URL}")
        
        # Raw SQL
        raw_count = db.execute(text("SELECT count(*) FROM rooms")).scalar()
        print(f"Raw SQL count: {raw_count}")
        
        # ORM
        orm_count = db.query(func.count(Room.id)).scalar()
        print(f"ORM count: {orm_count}")
        
        if raw_count != orm_count:
            print("MISMATCH DETECTED!")
            # Check table existence in current session
            tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
            print(f"Tables in public schema: {[t[0] for t in tables]}")
            
    finally:
        db.close()

if __name__ == "__main__":
    debug()
