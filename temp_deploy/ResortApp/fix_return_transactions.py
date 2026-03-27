import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import app modules
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL

def fix_return_transactions():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("Checking for legacy 'return' transactions...")
        
        # Find transactions with 'return' type
        query = text("SELECT id, reference_number, notes FROM inventory_transactions WHERE transaction_type = 'return'")
        result = db.execute(query)
        transactions = result.fetchall()
        
        if not transactions:
            print("No 'return' transactions found. Nothing to fix.")
            return

        print(f"Found {len(transactions)} 'return' transactions to fix.")
        
        # Update them to 'transfer_in'
        update_query = text("UPDATE inventory_transactions SET transaction_type = 'transfer_in' WHERE transaction_type = 'return'")
        db.execute(update_query)
        db.commit()
        
        print("Successfully updated transaction types to 'transfer_in'.")
        print("Please refresh the Inventory Dashboard to see positive values.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_return_transactions()
