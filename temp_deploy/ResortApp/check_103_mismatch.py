from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.models.room import Room
import json
from app.api.inventory import get_location_items
from sqlalchemy.orm import Session

def check_103_mismatch():
    db = SessionLocal()
    
    # 1. Get Room and Location ID
    room = db.query(Room).filter(Room.number == '103').first()
    if not room or not room.inventory_location_id:
        print("Room 103 not found or has no inventory location")
        return

    loc_id = room.inventory_location_id
    print(f"Room 103 | Location ID: {loc_id}")

    # 2. Get Last Checkout Request
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == '103', 
        CheckoutRequest.status == 'completed'
    ).order_by(CheckoutRequest.id.desc()).first()

    if req:
        print("\n--- LAST CHECKOUT REQUEST DATA ---")
        print(f"Request ID: {req.id}")
        data = req.inventory_data
        for item in data:
            name = item.get('item_name', 'Unknown')
            used = item.get('used_qty', 0)
            missing = item.get('missing_qty', 0)
            damage = item.get('damage_qty', 0)
            stock = item.get('allocated_stock', 0)
            is_rent = item.get('is_rentable', False)
            is_fixed = item.get('is_fixed_asset', False)
            print(f"- {name:20} | Stock: {stock} | Used: {used} | Missing: {missing} | Damage: {damage} | Rent: {is_rent} | Fixed: {is_fixed}")
    else:
        print("No completed checkout request found for Room 103")

    # 3. Get Live Inventory Items
    print("\n--- LIVE INVENTORY (get_location_items) ---")
    items_response = get_location_items(loc_id, db)
    live_items = items_response.get('items', [])
    for item in live_items:
        name = item.get('item_name', item.get('name', 'Unknown'))
        qty = item.get('current_stock', 0)
        source = item.get('source', 'Unknown')
        is_fixed = item.get('is_fixed_asset', False)
        is_rent = item.get('is_rentable', False)
        print(f"- {name:25} | Qty: {qty} | Rent: {is_rent:5} | Fixed: {is_fixed:5} | Source: {source}")

    db.close()

if __name__ == "__main__":
    check_103_mismatch()
