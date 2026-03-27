import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.room import Room
# Location is in models.inventory
from app.models.inventory import Location

def inspect_test_data():
    db = SessionLocal()
    try:
        print("--- Searching for 'Test' Entities ---")
        
        # Check Locations
        locations = db.query(Location).filter(Location.name.ilike("%test%")).all()
        print(f"Found {len(locations)} Location(s) matching '%test%':")
        for loc in locations:
            print(f" - [Location ID: {loc.id}] {loc.name} (Type: {loc.location_type})")
            
        # Check Rooms
        rooms = db.query(Room).filter(Room.room_number.ilike("%test%")).all()
        print(f"Found {len(rooms)} Room(s) matching '%test%':")
        for room in rooms:
            print(f" - [Room ID: {room.id}] {room.room_number}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_test_data()
