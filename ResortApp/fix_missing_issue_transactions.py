
import sys
import os
from datetime import timezone, datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import StockIssue, StockIssueDetail, InventoryTransaction, Location

def fix_missing_issue_transactions():
    """
    Scans for StockIssue records that were created by seed scripts but did not generate corresponding
    InventoryTransaction records. Creates these transactions for proper history log.
    """
    db = SessionLocal()
    try:
        print("Starting Transaction Log Fix for Stock Issues...")
        
        # 1. Get all Stock Issues
        issues = db.query(StockIssue).all()
        
        created_count = 0
        
        for issue in issues:
            # Check if transactions already exist for this issue
            # We use the issue number in notes or ref number to identify
            
            # Simple check: Does any transaction exist referring to this issue number?
            existing_tx = db.query(InventoryTransaction).filter(
                InventoryTransaction.reference_number == issue.issue_number
            ).first()
            
            if existing_tx:
                continue # Already processed
                
            print(f"Processing Issue: {issue.issue_number}...")
            
            source_loc = db.query(Location).filter(Location.id == issue.source_location_id).first()
            dest_loc = db.query(Location).filter(Location.id == issue.destination_location_id).first()
            
            source_name = source_loc.name if source_loc else "Unknown Source"
            dest_name = dest_loc.name if dest_loc else "Unknown Destination"
            
            # For each detail line in the issue
            details = db.query(StockIssueDetail).filter(StockIssueDetail.issue_id == issue.id).all()
            
            for detail in details:
                # 1. Transaction OUT from Source (Warehouse)
                tx_out = InventoryTransaction(
                    item_id=detail.item_id,
                    transaction_type="transfer_out",
                    quantity=detail.issued_quantity,
                    unit_price=detail.unit_price,
                    total_amount=detail.cost,
                    reference_number=issue.issue_number,
                    department=dest_name, # Where it went
                    notes=f"Stock Issue: {issue.issue_number} -> {dest_name}",
                    created_by=issue.issued_by,
                    created_at=issue.issue_date or datetime.now(timezone.utc)
                )
                db.add(tx_out)
                
                # 2. Transaction IN to Destination (Room)
                tx_in = InventoryTransaction(
                    item_id=detail.item_id,
                    transaction_type="transfer_in",
                    quantity=detail.issued_quantity,
                    unit_price=detail.unit_price,
                    total_amount=detail.cost,
                    reference_number=issue.issue_number,
                    department=dest_name, 
                    notes=f"Stock Received from {source_name} (Issue: {issue.issue_number})",
                    created_by=issue.issued_by,
                    created_at=issue.issue_date or datetime.now(timezone.utc)
                )
                db.add(tx_in)
                
                created_count += 2
                
        db.commit()
        print(f"\nSUCCESS: Created {created_count} transaction logs for existing Stock Issues.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_missing_issue_transactions()
