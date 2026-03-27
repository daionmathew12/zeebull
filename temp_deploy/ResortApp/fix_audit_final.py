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
    
    if not req: return

    print(f"Fixing audit for Room 103")
    
    items = req.inventory_data or []
    fixed_items = []
    
    # Track items we've already allocated fully
    allocated_map = {} # item_id -> total_allocated
    
    for item in items:
        iid = item.get('item_id')
        name = item.get('item_name', '').lower()
        is_rent = item.get('is_rentable', False)
        
        # Rule for TV: physically only 1 exists
        if iid == 4: # Smart TV
            if is_rent:
                item['allocated_stock'] = 1.0
            else:
                item['allocated_stock'] = 0.0 # Don't duplicate the count
                
        # Rule for Bulbs: physically 2 exist
        if iid == 22:
             # Already fixed to 1.0 + 1.0 = 2.0 total in previous run?
             # Let's be explicit
             if is_rent: item['allocated_stock'] = 1.0
             else: item['allocated_stock'] = 1.0
        
        fixed_items.append(item)
    
    req.inventory_data = fixed_items
    db.commit()
    print("Done")
    db.close()

if __name__ == "__main__":
    fix_audit()
