from app.database import SessionLocal
from app.models.inventory import InventoryTransaction, StockIssue

db = SessionLocal()
try:
    print("Updating transaction types for stock transfers...")
    
    # Get all stock issues with destinations (transfers)
    transfers = db.query(StockIssue).filter(
        StockIssue.destination_location_id.isnot(None)
    ).all()
    
    count = 0
    for transfer in transfers:
        # Update all OUT transactions for this transfer to transfer_out
        txns = db.query(InventoryTransaction).filter(
            InventoryTransaction.reference_number == transfer.issue_number,
            InventoryTransaction.transaction_type == "out"
        ).all()
        
        for txn in txns:
            print(f"Updating transaction {txn.id} for {transfer.issue_number}: out -> transfer_out")
            txn.transaction_type = "transfer_out"
            count += 1
    
    db.commit()
    print(f"\nUpdated {count} transactions from 'out' to 'transfer_out'")
    print("These are stock transfers, not consumption.")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
