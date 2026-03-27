from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.models.room import Room
import json

def patch_checkout_103():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == '103').first()
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == '103', 
        CheckoutRequest.status == 'completed'
    ).order_by(CheckoutRequest.id.desc()).first()
    
    if req:
        print(f"Found Req ID: {req.id}")
        data = req.inventory_data
        updated = False
        for item in data:
            name = str(item.get('item_name', '')).lower()
            if 'smart tv' in name or 'led bulb' in name:
                # Use mapped_asset_qty to distinguish
                mapped_qty = float(item.get('mapped_asset_qty', 0))
                is_rent = item.get('is_rentable', False)
                is_fixed = item.get('is_fixed_asset', False)
                
                if mapped_qty > 0:
                    if is_rent:
                        print(f"Fixing {name}: marking NOT rentable (Fixed Asset)")
                        item['is_rentable'] = False
                        item['is_fixed_asset'] = True
                        updated = True
                else:
                    if not is_rent:
                        print(f"Fixing {name}: marking AS rentable (Issued Rental)")
                        item['is_rentable'] = True
                        item['is_fixed_asset'] = False
                        updated = True
        
        if updated:
            req.inventory_data = data
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(req, "inventory_data")
            db.commit()
            print("Successfully patched inventory_data for Room 103")
        else:
            print("No updates needed for Room 103 inventory_data")
    else:
        print("No completed checkout request found for Room 103")
    db.close()

if __name__ == "__main__":
    patch_checkout_103()
