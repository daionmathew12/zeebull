import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import Location

def delete_target_location():
    db = SessionLocal()
    try:
        print("--- Deleting 'Test Room Loc' ---")
        
        loc = db.query(Location).filter(Location.id == 22).first()
        if not loc:
            print("Location ID 22 not found.")
            return
            
        if loc.name != "Test Room Loc":
            print(f"WARNING: Location 22 is named '{loc.name}', not 'Test Room Loc'. Aborting for safety.")
            return
            
        db.delete(loc)
        db.commit()
        print(f"SUCCESS: Deleted Location '{loc.name}' (ID: 22).")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_target_location()
