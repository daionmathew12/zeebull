from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.models.room import Room
import json

def check_103_mismatch():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == '103').first()
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == '103', 
        CheckoutRequest.status == 'completed'
    ).order_by(CheckoutRequest.id.desc()).first()

    if req:
        print(f"REQ_ID: {req.id}")
        data = req.inventory_data
        print("CHECKOUT_ITEMS:")
        for item in data:
            print(f"ID:{item.get('item_id')} NAME:{item.get('item_name')} U:{item.get('used_qty')} M:{item.get('missing_qty')} D:{item.get('damage_qty')} R:{item.get('is_rentable')} F:{item.get('is_fixed_asset')}")
    else:
        print("NO_REQ")

    from app.models.inventory import LocationStock, InventoryItem
    stocks = db.query(LocationStock).filter(LocationStock.location_id == room.inventory_location_id).all()
    print("LIVE_STOCKS:")
    for s in stocks:
        item = db.query(InventoryItem).filter(InventoryItem.id == s.item_id).first()
        print(f"ID:{s.item_id} NAME:{item.name if item else 'NA'} QTY:{s.quantity}")

    db.close()

if __name__ == "__main__":
    check_103_mismatch()
