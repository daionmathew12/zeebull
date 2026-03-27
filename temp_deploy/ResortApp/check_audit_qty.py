from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
import json

def check_audit():
    db = SessionLocal()
    # Find active booking for 103
    room_number = "103"
    
    # Get latest completed checkout request for this room
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == room_number,
        CheckoutRequest.status == "completed"
    ).order_by(CheckoutRequest.id.desc()).first()
    
    if not req:
        print(f"No completed checkout request found for room {room_number}")
        return

    print(f"Checkout Request ID: {req.id}")
    
    # Analyze LED Bulb specifically
    items = req.inventory_data or []
    
    print(f"Total entries in audit data: {len(items)}")
    
    targets = ["led", "tv", "towel"]
    for target in targets:
        entries = [i for i in items if target in i.get('item_name', '').lower()]
        print(f"\n--- {target.upper()} entries ---")
        for i, e in enumerate(entries):
             name = e.get('item_name')
             iid = e.get('item_id')
             u = e.get('used_qty')
             a = e.get('allocated_stock')
             r = e.get('is_rentable')
             f = e.get('is_fixed_asset')
             print(f"  {i+1}: ID:{iid} | {name} | use:{u} | alloc:{a} | rent:{r} | fix:{f}")

    db.close()

if __name__ == "__main__":
    check_audit()
