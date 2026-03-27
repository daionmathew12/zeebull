from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
import os

def check_audit():
    db = SessionLocal()
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == "103",
        CheckoutRequest.status == "completed"
    ).order_by(CheckoutRequest.id.desc()).first()
    
    with open("/home/basilabrahamaby/audit_report.txt", "w") as f:
        if not req:
            f.write("NONE\n")
            return

        for item in req.inventory_data or []:
            i = item
            line = f"ITEM:{i.get('item_name')}|ID:{i.get('item_id')}|ALLOC:{i.get('allocated_stock')}|USED:{i.get('used_qty')}|MISS:{i.get('missing_qty')}|DMG:{i.get('damage_qty')}|RENT:{i.get('is_rentable')}|FIXED:{i.get('is_fixed_asset')}\n"
            f.write(line)
    db.close()

if __name__ == "__main__":
    check_audit()
