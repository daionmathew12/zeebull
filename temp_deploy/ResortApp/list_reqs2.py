from app.database import SessionLocal
from app.models.checkout import CheckoutRequest

db = SessionLocal()
srs = db.query(CheckoutRequest).all()
for sr in srs:
    print(f"ID: {sr.id} (Returned as {sr.id + 1000000}), Status: {sr.status}, Room: {sr.room_number}")
db.close()
