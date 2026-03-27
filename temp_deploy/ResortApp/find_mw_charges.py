from app.database import SessionLocal
from app.models.checkout import CheckoutRequest

def debug():
    db = SessionLocal()
    try:
        req = db.query(CheckoutRequest).filter(CheckoutRequest.id == 1).first()
        for item in req.inventory_data:
            if str(item.get("item_id")) == "4":
                print(f"Mineral Water Audit Keys: {item.keys()}")
                print(f"  damage_charge: {item.get('damage_charge')}")
                print(f"  missing_item_charge: {item.get('missing_item_charge')}")
                print(f"  total_charge: {item.get('total_charge')}")
                print(f"  selling_price: {item.get('selling_price')}")
                print(f"  unit_price: {item.get('unit_price')}")
    finally:
        db.close()

if __name__ == "__main__":
    debug()
