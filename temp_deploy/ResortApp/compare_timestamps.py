from app.database import SessionLocal
from app.models.inventory import InventoryTransaction

db = SessionLocal()
try:
    # Check all transactions for ISS-20251209-001
    all_txns = db.query(InventoryTransaction).filter(
        InventoryTransaction.reference_number == "ISS-20251209-001"
    ).order_by(InventoryTransaction.id).all()
    
    print(f"All transactions for ISS-20251209-001: {len(all_txns)}\n")
    
    for txn in all_txns:
        print(f"ID: {txn.id} | Type: {txn.transaction_type:15} | Item: {txn.item_id} | Created: {txn.created_at}")
        
finally:
    db.close()
