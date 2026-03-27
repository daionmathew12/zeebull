from app.database import SessionLocal
from app.models.inventory import InventoryTransaction

db = SessionLocal()
try:
    # Get all transfer_in transactions
    transfer_in_txns = db.query(InventoryTransaction).filter(
        InventoryTransaction.transaction_type == "transfer_in"
    ).all()
    
    print(f"Fixing timestamps for {len(transfer_in_txns)} transfer_in transactions...")
    
    for txn in transfer_in_txns:
        # Find the corresponding transfer_out transaction
        transfer_out = db.query(InventoryTransaction).filter(
            InventoryTransaction.reference_number == txn.reference_number,
            InventoryTransaction.item_id == txn.item_id,
            InventoryTransaction.transaction_type == "transfer_out"
        ).first()
        
        if transfer_out:
            print(f"Updating txn {txn.id}: {txn.created_at} -> {transfer_out.created_at}")
            txn.created_at = transfer_out.created_at
        else:
            print(f"No matching transfer_out found for txn {txn.id}")
    
    db.commit()
    print("\nTimestamps fixed!")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
