
import sys
import os

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.account import JournalEntry, JournalEntryLine
from app.models.inventory import StockIssue

def fix_incorrect_cogs():
    db = SessionLocal()
    try:
        print("--- Fixing Incorrect COGS Entries ---")
        
        # 1. Identify Stock Issues that are Transfers (have destination) but have Consumption Journal Entries
        issues = db.query(StockIssue).filter(StockIssue.destination_location_id != None).all()
        
        fixed_count = 0
        
        for issue in issues:
            # Check for consumption journal entry
            jes = db.query(JournalEntry).filter(
                JournalEntry.reference_type == 'consumption',
                JournalEntry.reference_id == issue.id
            ).all()
            
            for je in jes:
                print(f"Found Incorrect J.E. for Issue #{issue.id} (Ref: {issue.issue_number}) -> J.E. #{je.id}")
                # Delete lines and entry
                db.query(JournalEntryLine).filter(JournalEntryLine.entry_id == je.id).delete()
                db.delete(je)
                fixed_count += 1
        
        db.commit()
        print(f"Successfully deleted {fixed_count} incorrect journal entries.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_incorrect_cogs()
