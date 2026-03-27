
import sys
import os
from sqlalchemy import func

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryTransaction

def analyze_transaction_sums():
    db = SessionLocal()
    try:
        print("--- Analyzing Transaction Sums by Type ---")
        results = db.query(
            InventoryTransaction.transaction_type,
            func.sum(InventoryTransaction.total_amount),
            func.count(InventoryTransaction.id)
        ).group_by(InventoryTransaction.transaction_type).all()

        for txn_type, total, count in results:
            print(f"Type: '{txn_type}' | Count: {count} | Total Amount: {total:,.2f}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze_transaction_sums()
