from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
import json

def dump_audit():
    db = SessionLocal()
    req = db.query(CheckoutRequest).filter(
        CheckoutRequest.room_number == "103",
        CheckoutRequest.status == "completed"
    ).order_by(CheckoutRequest.id.desc()).first()
    
    if req:
        print(json.dumps(req.inventory_data, indent=2))
    else:
        print("No request found")
    db.close()

if __name__ == "__main__":
    dump_audit()
