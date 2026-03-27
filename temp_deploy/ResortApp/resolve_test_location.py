import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.room import Room
from app.models.inventory import Location

def resolve_test_location():
    db = SessionLocal()
    try:
        print("--- Resolving Test Location Dependencies ---")
        
        # Get Location
        loc = db.query(Location).filter(Location.id == 22).first()
        if not loc: 
            print("Location 22 already gone.")
            return

        print(f"Target: Location {loc.id} ({loc.name})")

        # Get Linking Room
        room = db.query(Room).filter(Room.inventory_location_id == 22).first()
        
        if room:
            print(f"Linked Room found: [ID: {room.id}] Number: '{room.number}'")
            
            if "test" in room.number.lower():
                print("Room appears to be a TEST room. Deleting Room...")
                db.delete(room)
                # Note: Deleting Room might cascade to BookingRoom etc. 
                # Model says: cascade="all, delete-orphan". So safe.
            else:
                print("Room appears to be REAL. Unlinking Location...")
                room.inventory_location_id = None
                db.add(room)
            
            db.commit() # Commit room change
            print("Room dependency resolved.")
            
        else:
            print("No linked room found (weird, error said there was one).")
        
        # Now delete Location
        print("Deleting Location...")
        db.delete(loc)
        db.commit()
        print("SUCCESS: 'Test Room Loc' deleted.")

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    resolve_test_location()
