from app.database import SessionLocal
from app.models.inventory import StockIssue
from app.models.account import JournalEntry
from app.utils.accounting_helpers import create_consumption_journal_entry

db = SessionLocal()
try:
    print("Checking for missing consumption journal entries...")
    issues = db.query(StockIssue).all()
    count = 0
    for issue in issues:
        # Check if JE exists
        je = db.query(JournalEntry).filter(
            JournalEntry.reference_type == 'consumption',
            JournalEntry.reference_id == issue.id
        ).first()
        
        if not je:
            print(f"Backfilling JE for Issue #{issue.issue_number}")
            for detail in issue.details:
                if detail.cost and detail.cost > 0:
                    try:
                        # Fetch item name - assuming relationships loaded or lazy load
                        item_name = detail.item.name if detail.item else "Unknown Item"
                        
                        create_consumption_journal_entry(
                            db=db,
                            consumption_id=issue.id,
                            cogs_amount=float(detail.cost),
                            inventory_item_name=item_name,
                            created_by=issue.issued_by
                        )
                        count += 1
                    except Exception as e:
                        print(f"Error backfilling JE for detail {detail.id}: {e}")
    db.commit()
    print(f"Backfill complete. Created {count} journal entries.")

except Exception as e:
    print(f"Global Error: {e}")
    db.rollback()
finally:
    db.close()
