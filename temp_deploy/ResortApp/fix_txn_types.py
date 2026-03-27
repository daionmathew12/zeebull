from app.database import SessionLocal
from app.models.inventory import InventoryTransaction

db = SessionLocal()

def fix_transaction_types():
    print("--- Fixing Transaction Types for Asset Assignments ---")
    
    # We look for transactions created by our backfill or asset assignment logic
    # They generally have "Asset Assigned to" in notes.
    
    transactions = db.query(InventoryTransaction).filter(
        InventoryTransaction.notes.like("%Asset Assigned to%")
    ).all()
    
    count = 0
    for txn in transactions:
        # 1. Fix Type: 'out' or 'Transfer Out' -> 'transfer_out'
        if txn.transaction_type in ["out", "Transfer Out"]:
            print(f"Updating Transaction {txn.id} (Ref: {txn.reference_number}): {txn.transaction_type} -> transfer_out")
            txn.transaction_type = "transfer_out"
            count += 1
            
        # 2. Ensure Paired 'transfer_in' exists
        if txn.transaction_type == "transfer_out" and txn.reference_number:
            # Check for IN txn with same ref
            exists_in = db.query(InventoryTransaction).filter(
                InventoryTransaction.reference_number == txn.reference_number,
                InventoryTransaction.transaction_type == "transfer_in"
            ).first()
            
            if not exists_in:
                print(f"Creating missing 'transfer_in' for {txn.reference_number}")
                
                # Parse destination from notes "Asset Assigned to X"
                dest_name = "Unknown Location"
                if "Asset Assigned to " in (txn.notes or ""):
                    dest_name = txn.notes.split("Asset Assigned to ")[1].strip()
                
                txn_in = InventoryTransaction(
                    item_id=txn.item_id,
                    transaction_type="transfer_in",
                    quantity=txn.quantity,
                    unit_price=txn.unit_price,
                    total_amount=txn.total_amount,
                    reference_number=txn.reference_number,
                    department=dest_name, 
                    notes=f"Asset Received from Central Warehouse",
                    created_by=txn.created_by
                )
                db.add(txn_in)
                count += 1
            
    db.commit()
    print(f"--- Updated {count} transactions. ---")

if __name__ == "__main__":
    fix_transaction_types()
