
import sys
import os
from sqlalchemy import func

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryTransaction, InventoryItem

def analyze_specific_consumption():
    db = SessionLocal()
    try:
        print("--- Analyzing COGS Transactions (Ref #12 and others) ---")
        
        # Look for the specific amounts or reference 12
        # We know one is 1000 and another is 1800, total 2800.
        
        transactions = db.query(InventoryTransaction)\
            .join(InventoryItem)\
            .filter(InventoryTransaction.transaction_type == 'out')\
            .all()

        for t in transactions:
            print(f"ID: {t.id} | Type: {t.transaction_type} | Item: {t.item.name} | Qty: {t.quantity} | Amount: {t.total_amount} | Ref: {t.reference_number} | Notes: {t.notes}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze_specific_consumption()
