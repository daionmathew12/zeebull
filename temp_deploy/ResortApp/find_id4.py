from app.database import SessionLocal
from app.models.checkout import CheckoutRequest

def debug():
    db = SessionLocal()
    try:
        req = db.query(CheckoutRequest).filter(CheckoutRequest.id == 1).first()
        if not req or not req.inventory_data:
            print("No request found")
            return
        
        for item in req.inventory_data:
            it_id = item.get("item_id")
            if str(it_id) == "4" or it_id == 4:
                print(f"FOUND ID 4: {item}")
    finally:
        db.close()

if __name__ == "__main__":
    debug()
