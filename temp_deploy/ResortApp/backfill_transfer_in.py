from app.database import SessionLocal
from app.models.inventory import StockIssue, InventoryTransaction, Location
from datetime import datetime

db = SessionLocal()
try:
    print("Backfilling missing transfer_in transactions...")
    
    # Get all stock issues
    issues = db.query(StockIssue).all()
    
    count = 0
    for issue in issues:
        # Check if this issue has a destination
        if not issue.destination_location_id:
            continue
            
        # Get destination location
        dest_location = db.query(Location).filter(Location.id == issue.destination_location_id).first()
        if not dest_location:
            continue
            
        dest_location_name = f"{dest_location.building} - {dest_location.room_area}" if dest_location.building or dest_location.room_area else dest_location.name or f"Location {dest_location.id}"
        
        # For each detail in the issue
        for detail in issue.details:
            # Check if transfer_in transaction already exists
            existing = db.query(InventoryTransaction).filter(
                InventoryTransaction.reference_number == issue.issue_number,
                InventoryTransaction.item_id == detail.item_id,
                InventoryTransaction.transaction_type == "transfer_in"
            ).first()
            
            if not existing:
                # Create the transfer_in transaction
                transaction_in = InventoryTransaction(
                    item_id=detail.item_id,
                    transaction_type="transfer_in",
                    quantity=detail.issued_quantity,
                    unit_price=detail.unit_price,
                    total_amount=detail.cost,
                    reference_number=issue.issue_number,
                    notes=f"Stock Received: {issue.issue_number} from {issue.source_location_id or 'Central'}",
                    created_by=issue.issued_by,
                    department=dest_location_name,
                    created_at=issue.issue_date
                )
                db.add(transaction_in)
                count += 1
                print(f"Created transfer_in for Issue {issue.issue_number}, Item {detail.item_id}")
    
    db.commit()
    print(f"\nBackfill complete. Created {count} transfer_in transactions.")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
