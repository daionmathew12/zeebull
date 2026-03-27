
import sys
import os
from sqlalchemy import func

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.account import AccountLedger, JournalEntry, JournalEntryLine

def explain_cogs_entries():
    db = SessionLocal()
    try:
        print("--- Details of COGS (₹2,800.00) ---")
        
        # 1. Find COGS Ledger ID
        cogs_ledger = db.query(AccountLedger).filter(AccountLedger.name.ilike("%Cost of Goods Sold%")).first()
        if not cogs_ledger:
            print("COGS Ledger not found!")
            return

        print(f"COGS Ledger ID: {cogs_ledger.id}")

        # 2. Find Lines
        lines = db.query(JournalEntryLine, JournalEntry)\
            .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)\
            .filter(JournalEntryLine.debit_ledger_id == cogs_ledger.id)\
            .all()

        total = 0
        for line, entry in lines:
            print(f"Date: {entry.entry_date} | Amount: ₹{line.amount:,.2f} | Desc: {entry.description} | Ref: {entry.reference_type} #{entry.reference_id}")
            total += float(line.amount)

        print(f"--------------------------------------------------")
        print(f"Total COGS found in Journal: ₹{total:,.2f}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    explain_cogs_entries()
