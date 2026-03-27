from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
import json

def check_data():
    db = SessionLocal()
    reqs = db.query(CheckoutRequest).order_by(CheckoutRequest.id.desc()).limit(5).all()
    
    for req in reqs:
        print(f"--- Request ID: {req.id} | Room: {req.room_number} | Guest: {req.guest_name} ---")
        # print("Inventory Data Snippet:")
        # print(json.dumps(req.inventory_data[:1] if req.inventory_data else [], indent=2))
        if req.inventory_data:
            for item in req.inventory_data:
                print(f"--- Inventory Item: {item.get('item_name')} (ID: {item.get('item_id')}) ---")
                print(f"    Used: {item.get('used_qty')}, Damaged: {item.get('damage_qty')}, Missing: {item.get('missing_qty')}")
                print(f"    Allocated: {item.get('allocated_stock')}, Comp Limit: {item.get('complimentary_qty')}")
                print(f"    Charges -> Damage: {item.get('damage_charge')}, Missing: {item.get('missing_item_charge')}")
                print("-" * 30)


    
    db.close()

if __name__ == "__main__":
    check_data()
