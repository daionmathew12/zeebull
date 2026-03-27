from app.database import SessionLocal
from app.api.checkout import get_checkout_request_inventory_details
from app.models.checkout import CheckoutRequest
from app.models.user import User
import json

def test_api():
    db = SessionLocal()
    # Find req for 102
    req = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == '102').order_by(CheckoutRequest.id.desc()).first()
    user = db.query(User).first()
    
    res = get_checkout_request_inventory_details(req.id, db, user)
    print(json.dumps(res, indent=2))
    db.close()

if __name__ == "__main__":
    test_api()
