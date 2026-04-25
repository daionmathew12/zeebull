import os
import sys

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.booking import _fetch_inventory
from app.models.booking import Booking, BookingRoom
from app.models.inventory import AssetMapping

def verify():
    db = SessionLocal()
    # Find a booking that has rooms
    b = db.query(Booking).join(Booking.booking_rooms).first()
    if b:
        room_ids = [br.room_id for br in b.booking_rooms]
        print(f"Checking booking {b.id} with rooms {room_ids}")
        
        # Check if there are any AssetMappings for these rooms
        from app.models.room import Room
        rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
        loc_ids = [r.inventory_location_id for r in rooms if r.inventory_location_id]
        
        mappings = db.query(AssetMapping).filter(AssetMapping.location_id.in_(loc_ids)).all()
        print(f"Found {len(mappings)} AssetMappings for locations {loc_ids}")
        
        inventory = _fetch_inventory(db, room_ids, b.check_in, b.check_out, booking_id=b.id)
        print(f"Fetched inventory count: {len(inventory)}")
        if inventory:
            for item in inventory[:5]: # Show first 5
                print(f"- {item.get('item_name')}: type={item.get('type')}, is_asset_fixed={item.get('is_asset_fixed')}")
        else:
            print("No inventory items found. This might be correct if no assets are mapped and no stock issued.")
    else:
        print("No booking with rooms found in database.")
    db.close()

if __name__ == "__main__":
    verify()
