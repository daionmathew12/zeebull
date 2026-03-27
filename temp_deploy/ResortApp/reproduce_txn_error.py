
import sys
import os

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryTransaction, User

def test_transactions():
    db = SessionLocal()
    item_id = 1
    try:
        # Simulate logic from get_item_transactions
        transactions = db.query(InventoryTransaction)\
            .filter(InventoryTransaction.item_id == item_id)\
            .order_by(InventoryTransaction.created_at.desc())\
            .all()
        
        print(f"Found {len(transactions)} transactions")
        
        result = []
        for txn in transactions:
            user = db.query(User).filter(User.id == txn.created_by).first() if txn.created_by else None
            
            # Construct dict roughly how backend does
            item_dict = {
                **txn.__dict__,
                "created_by_name": user.name if user else "System",
            }
            if "_sa_instance_state" in item_dict:
                del item_dict["_sa_instance_state"]
                
            print(f"Processed txn {txn.id}")
            result.append(item_dict)
            
        print("Success processing transactions")
        
        # Validate with pydantic
        from app.schemas.inventory import InventoryTransactionOut
        for r in result:
            InventoryTransactionOut(**r)
            
        print("Validation success")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_transactions()
