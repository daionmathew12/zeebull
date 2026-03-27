from app.database import SessionLocal
from app.models.account import JournalEntry
from app.models.inventory import StockIssue

db = SessionLocal()
try:
    print("Deleting incorrect COGS journal entries for stock transfers...")
    
    # Get all stock issues that have a destination location (transfers, not consumption)
    transfers = db.query(StockIssue).filter(
        StockIssue.destination_location_id.isnot(None)
    ).all()
    
    count = 0
    for transfer in transfers:
        # Find and delete the journal entry
        je = db.query(JournalEntry).filter(
            JournalEntry.reference_type == 'consumption',
            JournalEntry.reference_id == transfer.id
        ).first()
        
        if je:
            print(f"Deleting JE {je.entry_number} for transfer {transfer.issue_number}")
            db.delete(je)
            count += 1
    
    db.commit()
    print(f"\nDeleted {count} incorrect journal entries for transfers.")
    print("These were stock transfers, not consumption, so no COGS entry should exist.")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
