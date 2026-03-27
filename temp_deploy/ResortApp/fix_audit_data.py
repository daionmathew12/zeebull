from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
import json

def fix_audit():
    db = SessionLocal()
    room_number = "103"
    
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == room_number,
        CheckoutRequest.status == "completed"
    ).order_by(CheckoutRequest.id.desc()).first()
    
    if not req:
        print(f"No completed checkout request found for room {room_number}")
        return

    print(f"Fixing Checkout Request ID: {req.id}")
    
    items = req.inventory_data or []
    fixed_items = []
    
    # Track items we've already "halved" or fixed
    # The duplicate issue happened because total room stock was assigned to each row
    # In Image 1, room has 2 bulbs, 2 TVs.
    # Audit has 2 entries for each. Result was 2+2=4.
    # So we should set each entry's allocated_stock to 1 (if it's 2).
    
    for item in items:
        name = item.get('item_name', '').lower()
        alloc = item.get('allocated_stock', 0)
        
        # If it's a bulb or TV and alloc is 2, it's likely from the bug
        if ("led" in name or "tv" in name) and alloc == 2.0:
            print(f"  Fixing {item.get('item_name')}: allocated_stock 2.0 -> 1.0")
            item['allocated_stock'] = 1.0
        
        fixed_items.append(item)
    
    req.inventory_data = fixed_items
    db.commit()
    print("Repair complete.")
    db.close()

if __name__ == "__main__":
    fix_audit()
