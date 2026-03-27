import sys
import os
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models.inventory import StockIssueDetail

db = SessionLocal()
target_ids = [21, 23, 13, 22, 26, 31]

details = db.query(StockIssueDetail).filter(
    StockIssueDetail.item_id.in_(target_ids),
    StockIssueDetail.is_payable == True
).all()

print(f"Found {len(details)} incorrectly payable items.")

for d in details:
    print(f"Fixing DetID {d.id} Item {d.item_id} Payable: {d.is_payable} -> False")
    d.is_payable = False

db.commit()
print("Done.")
