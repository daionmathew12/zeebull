from app.database import SessionLocal
from app.models.checkout import CheckoutRequest

def check_audit():
    db = SessionLocal()
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == "103",
        CheckoutRequest.status == "completed"
    ).order_by(CheckoutRequest.id.desc()).first()
    
    if not req:
        print("No request found")
        return

    print(f"Request ID: {req.id}")
    data = req.inventory_data or []
    for i, item in enumerate(data):
        name = item.get('item_name')
        iid = item.get('item_id')
        alloc = item.get('allocated_stock')
        used = item.get('used_qty')
        miss = item.get('missing_qty')
        damage = item.get('damage_qty')
        is_rent = item.get('is_rentable')
        is_fixed = item.get('is_fixed_asset')
        note = item.get('notes')
        print(f"[{i}] {name} (ID:{iid}) | alloc:{alloc} | used:{used} | miss:{miss} | damage:{damage} | rent:{is_rent} | fixed:{is_fixed} | note:{note}")
    db.close()

if __name__ == "__main__":
    check_audit()
