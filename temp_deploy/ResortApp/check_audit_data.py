from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
import json

def check_audit_data():
    db = SessionLocal()
    # Find the most recent checkout request for room 102
    req = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == '102').order_by(CheckoutRequest.id.desc()).first()
    
    if req:
        print(f"Request ID: {req.id}")
        print(f"Room: {req.room_number}")
        print(f"Status: {req.status}")
        print("Inventory Data:")
        print(json.dumps(req.inventory_data, indent=2))
    else:
        print("No request found for room 102")
    db.close()

if __name__ == "__main__":
    check_audit_data()
