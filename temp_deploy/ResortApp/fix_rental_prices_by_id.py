import sys
import os
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models.inventory import StockIssueDetail

db = SessionLocal()
target_ids = [21, 23, 13, 22, 26, 31]

details = db.query(StockIssueDetail).filter(
    StockIssueDetail.item_id.in_(target_ids),
    StockIssueDetail.rental_price > 0
).all()

print(f"Found {len(details)} remaining invalid rentals.")

for d in details:
    print(f"Fixing DetID {d.id} Item {d.item_id} Rent {d.rental_price} -> 0.0")
    d.rental_price = 0.0

db.commit()
print("Done.")
