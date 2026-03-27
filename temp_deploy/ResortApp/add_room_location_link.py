"""
Script to add inventory_location_id column to rooms table
This links rooms to inventory locations for asset tracking
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from sqlalchemy import text

def add_room_location_column():
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='rooms' AND column_name='inventory_location_id'
        """))
        
        if result.fetchone():
            print("✓ Column 'inventory_location_id' already exists in rooms table")
            return
        
        # Add the column
        db.execute(text("""
            ALTER TABLE rooms 
            ADD COLUMN inventory_location_id INTEGER 
            REFERENCES locations(id)
        """))
        
        db.commit()
        print("✓ Successfully added 'inventory_location_id' column to rooms table")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Adding inventory_location_id column to rooms table...")
    add_room_location_column()
    print("Done!")

