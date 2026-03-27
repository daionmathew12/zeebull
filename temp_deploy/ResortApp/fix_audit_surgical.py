from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
import json

def fix_audit():
    db = SessionLocal()
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == "103",
        CheckoutRequest.status == "completed"
    ).order_by(CheckoutRequest.id.desc()).first()
    
    if not req: return

    print(f"Fixing audit for Room 103 (ID:{req.id})")
    
    # We want a CLEAN set.
    # Room 103 items:
    # 1. LED Bulb (ID 3): 2 units total. 1 Rented, 1 Fixed?
    # 2. Smart TV (ID 4): 1 unit total. 1 Rented.
    # 3. Bath Towel (ID 6): 1 unit. Rented.
    # 4. Mineral Water (ID 8): Consumable.
    
    new_data = [
        {"item_id": 3, "item_name": "LED Bulb", "allocated_stock": 1.0, "is_rentable": True, "used_qty": 0.0, "missing_qty": 0.0, "damage_qty": 1.0, "notes": "Rental bulb"},
        {"item_id": 3, "item_name": "LED Bulb", "allocated_stock": 1.0, "is_rentable": False, "is_fixed_asset": True, "used_qty": 0.0, "missing_qty": 0.0, "damage_qty": 0.0, "notes": "Fixed bulb"},
        {"item_id": 4, "item_name": "Smart TV", "allocated_stock": 1.0, "is_rentable": True, "used_qty": 0.0, "missing_qty": 1.0, "damage_qty": 0.0, "notes": "Rented TV"},
        {"item_id": 6, "item_name": "Bath towel", "allocated_stock": 1.0, "is_rentable": True, "used_qty": 0.0, "missing_qty": 0.0, "damage_qty": 0.0, "notes": "Rented towel"},
        {"item_id": 8, "item_name": "mineral water", "allocated_stock": 2.0, "is_rentable": False, "used_qty": 1.0, "missing_qty": 0.0, "damage_qty": 0.0}
    ]
    
    # Check for damages from asset_damages list to be consistent
    # Image showed Smart TV (Missing) and LED Bulb (Damaged).
    
    req.inventory_data = new_data
    db.commit()
    print("Done")
    db.close()

if __name__ == "__main__":
    fix_audit()
