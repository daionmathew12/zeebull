from app.database import SessionLocal
from app.models.room import Room
from app.models.inventory import InventoryItem, LocationStock
from sqlalchemy import or_

def fix_room_103_counts():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == '103').first()
    if not room:
        print("Room 103 not found")
        return
    
    loc_id = room.inventory_location_id
    print(f"Fixing counts for Room 103 (LocID: {loc_id})")

    # 1. Smart TV (ID: 4) - User says there are 2 (one damaged, one undamaged)
    tv_stock = db.query(LocationStock).filter(LocationStock.location_id == loc_id, LocationStock.item_id == 4).first()
    if tv_stock:
        print(f"Updating Smart TV stock from {tv_stock.quantity} to 2.0")
        tv_stock.quantity = 2.0
    else:
        print("Adding Smart TV stock of 2.0")
        db.add(LocationStock(location_id=loc_id, item_id=4, quantity=2.0))

    # 2. LED Bulb (ID: 3) - User says undamaged count is wrong. 
    # Mapped: 1, Rented: 1. Total physical should be 2.
    # If 1 is damaged, only 1 should be good.
    led_stock = db.query(LocationStock).filter(LocationStock.location_id == loc_id, LocationStock.item_id == 3).first()
    if led_stock:
        print(f"Current LED stock is {led_stock.quantity}")
        # If it's already 2.0, no change needed here, the code will handle the split show.
    else:
        print("Adding LED stock of 2.0")
        db.add(LocationStock(location_id=loc_id, item_id=3, quantity=2.0))

    db.commit()
    print("Room 103 counts fixed.")
    db.close()

if __name__ == "__main__":
    fix_room_103_counts()
