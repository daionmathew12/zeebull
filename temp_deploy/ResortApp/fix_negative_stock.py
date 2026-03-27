import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add parent directory to path
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL
from app.models.inventory import LocationStock, InventoryTransaction

def fix_negative_stock():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("--- FIXING NEGATIVE STOCK ---")

        neg_stocks = db.query(LocationStock).filter(LocationStock.quantity < 0).all()
        
        if not neg_stocks:
            print("No negative stock found.")
            return

        print(f"Found {len(neg_stocks)} items with negative stock. Fixing...")
        
        for stock in neg_stocks:
            correction_qty = abs(stock.quantity)
            old_qty = stock.quantity
            
            # 1. Update stock to 0
            stock.quantity = 0
            stock.last_updated = datetime.utcnow()
            
            # 2. Record Transaction
            txn = InventoryTransaction(
                item_id=stock.item_id,
                transaction_type="adjustment",
                quantity=correction_qty,
                unit_price=0, # Internal correction
                total_amount=0,
                reference_number="AUTO-FIX-NEG",
                notes=f"Auto-correction: Reset negative stock {old_qty} -> 0 for Loc {stock.location_id}",
                created_by=1 # System/Admin
            )
            db.add(txn)
            print(f"  - Corrected Loc {stock.location_id}, Item {stock.item_id}: {old_qty} -> 0")
            
        db.commit()
        print("Successfully corrected negative stocks.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_negative_stock()
