from app.database import SessionLocal
from app.api.checkout import _calculate_bill_for_single_room
import json

def test_bill():
    db = SessionLocal()
    room_number = "103"
    print(f"Testing bill for Room {room_number}")
    res = _calculate_bill_for_single_room(db, room_number)
    
    # charges is an object
    charges = res['charges']
    
    print("\n--- Rental Usage ---")
    for item in charges.inventory_usage:
        print(f"{item.get('item_name')} | Qty: {item.get('quantity')} | Charge: {item.get('rental_charge')} | Notes: {item.get('notes')}")
        
    print("\n--- Asset Damages ---")
    for dmg in charges.asset_damages:
        print(f"{dmg.get('item_name')} | Cost: {dmg.get('replacement_cost')} | Notes: {dmg.get('notes')}")
        
    db.close()

if __name__ == "__main__":
    test_bill()
