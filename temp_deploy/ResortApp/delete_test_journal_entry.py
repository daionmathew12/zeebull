"""
Script to delete the test journal entry (JE-2025-11-0001)
"""
from app.database import SessionLocal
from app.models.account import JournalEntry, JournalEntryLine

def delete_test_journal_entry():
    db = SessionLocal()
    try:
        # Find the test journal entry
        entry = db.query(JournalEntry).filter(
            JournalEntry.entry_number == "JE-2025-11-0001"
        ).first()
        
        if entry:
            print(f"Found entry: {entry.entry_number} - {entry.description}")
            print(f"Entry ID: {entry.id}")
            print(f"Entry Date: {entry.entry_date}")
            
            # Delete associated lines first (due to foreign key constraints)
            lines_deleted = db.query(JournalEntryLine).filter(
                JournalEntryLine.entry_id == entry.id
            ).delete()
            
            print(f"Deleted {lines_deleted} journal entry lines")
            
            # Delete the journal entry
            db.delete(entry)
            db.commit()
            
            print(f"✅ Successfully deleted journal entry {entry.entry_number}")
        else:
            print("❌ Journal entry JE-2025-11-0001 not found")
    
    except Exception as e:
        print(f"❌ Error deleting journal entry: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_test_journal_entry()
