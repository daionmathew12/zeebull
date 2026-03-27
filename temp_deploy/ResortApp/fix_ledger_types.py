
import sys
import os
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models.account import AccountLedger

def fix_ledger_types():
    db = SessionLocal()
    try:
        print("--- Checking and Fixing Ledger Types ---")
        
        # 1. Input Tax -> Debit (Asset)
        # Input Tax Credit is an Asset, so it should be Debit balance type
        input_ledgers = db.query(AccountLedger).filter(AccountLedger.name.like("Input%")).all()
        for l in input_ledgers:
            if l.balance_type != "debit":
                print(f"Fixing {l.name}: {l.balance_type} -> debit")
                l.balance_type = "debit"
            else:
                print(f"{l.name} is correct (debit)")
                
        # 2. Output Tax -> Credit (Liability)
        output_ledgers = db.query(AccountLedger).filter(AccountLedger.name.like("Output%")).all()
        for l in output_ledgers:
            if l.balance_type != "credit":
                 print(f"Fixing {l.name}: {l.balance_type} -> credit")
                 l.balance_type = "credit"

        # 3. Accounts Payable -> Credit (Liability)
        ap_check = db.query(AccountLedger).filter(AccountLedger.name.like("Accounts Payable%")).all()
        for l in ap_check:
            if l.balance_type != "credit":
                print(f"Fixing {l.name}: {l.balance_type} -> credit")
                l.balance_type = "credit"
            else:
                print(f"{l.name} is correct (credit)")

        db.commit()
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_ledger_types()
