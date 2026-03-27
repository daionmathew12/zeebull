
import sys
import os
from sqlalchemy import func

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.account import AccountLedger, JournalEntryLine, JournalEntry

def inspect_tax_ledgers():
    db = SessionLocal()
    try:
        print("--- Inspecting Tax & AP Ledgers ---")
        ledgers_to_check = ["Accounts Payable (Vendor)", "Input CGST", "Input SGST"]
        
        for name in ledgers_to_check:
            ledger = db.query(AccountLedger).filter(AccountLedger.name == name).first()
            if not ledger:
                print(f"Ledger {name} not found")
                continue
                
            print(f"\nLedger: {ledger.name} (ID: {ledger.id})")
            
            # Get all lines
            lines = db.query(JournalEntryLine).filter(
                (JournalEntryLine.debit_ledger_id == ledger.id) | 
                (JournalEntryLine.credit_ledger_id == ledger.id)
            ).all()
            
            total_debit = 0
            total_credit = 0
            
            for line in lines:
                je = db.query(JournalEntry).get(line.entry_id)
                type_str = "DR" if line.debit_ledger_id == ledger.id else "CR"
                if type_str == "DR": total_debit += line.amount
                else: total_credit += line.amount
                
                print(f"[{type_str}] {line.amount:,.2f} | Ref: {je.reference_type} #{je.reference_id} | Desc: {je.description}")
            
            print(f"Total Debits: {total_debit:,.2f}")
            print(f"Total Credits: {total_credit:,.2f}")
            print(f"Net Balance (Dr-Cr): {total_debit - total_credit:,.2f}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_tax_ledgers()
