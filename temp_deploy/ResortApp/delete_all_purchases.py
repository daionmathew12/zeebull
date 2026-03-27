from app.database import SessionLocal
from app.models.inventory import PurchaseMaster, PurchaseDetail, InventoryTransaction, InventoryItem, LocationStock
from sqlalchemy import text, func

def delete_all_purchases():
    db = SessionLocal()
    try:
        print("="*50)
        print("STARTING PURCHASE DELETION")
        print("="*50)

        # 1. Delete Inventory Transactions linked to purchases
        print("Deleting Inventory Transactions linked to purchases...")
        # Identifying transactions that are 'purchase' type OR have a purchase_master_id
        # We need to be careful not to delete manual 'in' transactions if they are not linked to a purchase, 
        # but usually 'in' is purchase or return.
        # Based on schema, transaction_type='purchase' is distinct.
        
        deleted_txns = db.query(InventoryTransaction).filter(
            (InventoryTransaction.transaction_type == 'purchase') | 
            (InventoryTransaction.purchase_master_id.isnot(None)) |
            (InventoryTransaction.reference_number.like('PO-%'))
        ).delete(synchronize_session=False)
        print(f"Deleted {deleted_txns} inventory transactions.")

        # 2. Delete Purchase Details and Masters
        print("Deleting Purchase Details...")
        deleted_details = db.query(PurchaseDetail).delete(synchronize_session=False)
        print(f"Deleted {deleted_details} purchase details.")

        print("Deleting Purchase Masters...")
        deleted_purchases = db.query(PurchaseMaster).delete(synchronize_session=False)
        print(f"Deleted {deleted_purchases} purchase records.")

        # 3. Reset Location Stock (Aggressive)
        # Since we lost the source of stock (Purchases), we cannot accurately know per-location stock 
        # derived from those purchases. We will reset all location stocks to 0 to be safe/clean.
        print("Resetting all Location Stock to 0...")
        updated_loc_stocks = db.query(LocationStock).update({LocationStock.quantity: 0}, synchronize_session=False)
        print(f"Updated {updated_loc_stocks} location stock records.")

        db.commit()

        # 4. Recalculate InventoryItem.current_stock
        print("Recalculating Global Inventory Item Stock...")
        # We rely on remaining transactions (adjustments, transfers, manual IN/OUT)
        
        items = db.query(InventoryItem).all()
        updates_count = 0
        
        for item in items:
            # Sum remaining IN transactions
            # Note: We need to handle OUT transactions too if we want a true stock, 
            # but usually 'current_stock' is net.
            # Let's look at `reset_stock_to_purchases.py` logic which did: 
            # in_total = sum(quantity) for types ["in", "purchase", "adjustment", "transfer_in"]
            # It ignored consumption! "As if nothing has been used"
            
            # Here, if we delete purchases, do we want to simulate "Net Stock"?
            # IF the user wants real stock, we should sum (IN + Purchase + Adjustment + TransferIn) - (OUT + TransferOut + Issue + Usage)
            # But the previous script `reset_stock_to_purchases` seemed to IGNORE usage.
            # I will follow standard logic:
            # Calculate total 'in' flow from remaining transactions.
            
            # Let's TRY to calculate net stock from remaining transactions.
            # If transactions are the source of truth:
            # Stock = IN - OUT
            
            in_types = ['in', 'adjustment', 'transfer_in'] # purchase is gone
            out_types = ['out', 'transfer_out', 'issue', 'usage', 'waste'] 
            
            total_in = db.query(func.sum(InventoryTransaction.quantity)).filter(
                InventoryTransaction.item_id == item.id,
                InventoryTransaction.transaction_type.in_(in_types)
            ).scalar() or 0.0
            
            total_out = db.query(func.sum(InventoryTransaction.quantity)).filter(
                InventoryTransaction.item_id == item.id,
                InventoryTransaction.transaction_type.in_(out_types)
            ).scalar() or 0.0
            
            new_stock = total_in - total_out
            if new_stock < 0:
                new_stock = 0 # Prevent negative stock artifacts
                
            if item.current_stock != new_stock:
                item.current_stock = new_stock
                updates_count += 1
        
        db.commit()
        print(f"Recalculated stock for {len(items)} items. Updates applied: {updates_count}")
        print("="*50)
        print("DONE")
        print("="*50)

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_purchases()
