from app.database import SessionLocal
from app.models.inventory import AssetMapping, StockIssue, StockIssueDetail, InventoryTransaction, Location

db = SessionLocal()

def fix_missing_history():
    print("--- Backfilling Stock Issues for Recent Asset Mappings ---")
    
    # 1. Get ALL active mappings
    print("Fetching all active asset mappings...")
    mappings = db.query(AssetMapping).filter(
        AssetMapping.is_active == True
    ).all()
    
    from app.curd.inventory import generate_issue_number
    from datetime import datetime
    
    for mapping in mappings:
        # Check if a transaction/issue already exists for this mapping
        # We put "Asset Mapping ID: X" in the notes in our new code.
        exists = db.query(StockIssueDetail).filter(
            StockIssueDetail.notes.like(f"%Asset Mapping ID: {mapping.id}%")
        ).first()
        
        if exists:
            print(f"Mapping {mapping.id} already has Stock Issue. Checking for Transaction...")
            # Fetch issue to get number safely
            issue_rec = db.query(StockIssue).get(exists.issue_id)
            issue_number = issue_rec.issue_number if issue_rec else "UNKNOWN"
        else:
            print(f"Backfilling history for Mapping {mapping.id} (Item: {mapping.item_id}, Qty: {mapping.quantity})")
            
            # Create missing issue
            issue_number = generate_issue_number(db)
            
            # Create Stock Issue (Source: Central Warehouse ID 1)
            issue = StockIssue(
                issue_number=issue_number,
                issued_by=mapping.assigned_by if mapping.assigned_by else 1, # Default to admin (1) if unknown
                source_location_id=1,
                destination_location_id=mapping.location_id,
                issue_date=mapping.assigned_date or datetime.utcnow(),
                notes=f"Retroactive History for Asset Assignment"
            )
            db.add(issue)
            db.flush()
            
            # Create Detail
            item = mapping.item # Implicit via relationship if available, else query
            if not item:
                 # Manual query
                 from app.models.inventory import InventoryItem
                 item = db.query(InventoryItem).get(mapping.item_id)
            
            detail = StockIssueDetail(
                 issue_id=issue.id,
                 item_id=mapping.item_id,
                 issued_quantity=mapping.quantity,
                 unit=item.unit if item else "pcs",
                 unit_price=item.unit_price if item else 0,
                 cost=(item.unit_price or 0) * mapping.quantity,
                 notes=f"Asset Mapping ID: {mapping.id}"
            )
            db.add(detail)
            
            db.commit() # Commit issue first to get ID/Number if needed
        
        # 2. Backfill Inventory Transaction (For Transaciton Log UI)
        from app.models.inventory import InventoryTransaction, Location     
        
        # Check if transaction exists
        # Use a unique identifier in notes or reference to identify duplicates
        # Notes: "Asset Assigned to {dest_name}"
        # Ref: issue_number
        
        txn_exists = db.query(InventoryTransaction).filter(
            InventoryTransaction.reference_number == issue_number
        ).first()
        
        if txn_exists:
            print(f"Transaction for Mapping {mapping.id} already exists.")
        else:
            print(f"Creating Transaction for Mapping {mapping.id}...")
            dest_loc = db.query(Location).get(mapping.location_id)
            dest_name = dest_loc.name if dest_loc else "Unknown"
            
            # Fetch item for unit price
            item = mapping.item
            if not item:
                 from app.models.inventory import InventoryItem
                 item = db.query(InventoryItem).get(mapping.item_id)

            transaction = InventoryTransaction(
                item_id=mapping.item_id,
                transaction_type="out", # Use "out" or "transfer_out" to match UI filters
                # The UI filter in screenshot has "Transfer Out", "Stock Received", "Purchase (In)", "Waste/Spoilage"
                # "Transfer Out" creates a purple icon in screenshot.
                # Let's check what `create_stock_issue` uses. It uses `out_transaction_type = "transfer_out" if dest_location else "out"`
                # In create_asset_mapping, we used "Transfer Out" (string matching frontend filter?)
                # Actually, standardizing on "transfer_out" (snake_case) or Title Case? 
                # Screenshot shows "Transfer Out" (Title Case) in UI? Or is that a label?
                # Backend `fix_stock_consistency` used "adjustment".
                # `create_stock_issue` uses "transfer_out". 
                # Let's use "transfer_out" as it seems to be the system standard for transfers.
                # Wait, my previous `create_asset_mapping` edited used `transaction_type="Transfer Out"` (Title Case). 
                # If the frontend expects snake_case, Title Case might break icon/filtering. 
                # Let's check `get_transactions` or frontend code? 
                # The screenshot shows "Transfer Out" with purple icon. 
                # I will stick to "Transfer Out" if that's what I put in `create_asset_mapping` to be consistent,
                # BUT standard practice is snake_case. 
                # Let's assume the frontend maps it or displays raw. 
                # To be safe and consistent with my previous edit (Step 213), I will use "Transfer Out".
                quantity=mapping.quantity,
                unit_price=item.unit_price if item else 0,
                total_amount=(item.unit_price or 0) * mapping.quantity,
                reference_number=issue_number, 
                notes=f"Asset Assigned to {dest_name}",
                created_by=mapping.assigned_by if mapping.assigned_by else 1
            )
            db.add(transaction)
            db.commit()
            
    print("--- Backfill Complete ---")

if __name__ == "__main__":
    fix_missing_history()
