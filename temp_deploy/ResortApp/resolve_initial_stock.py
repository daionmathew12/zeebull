
import sys
import os
from sqlalchemy import func
from datetime import datetime

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.account import AccountLedger, AccountGroup, JournalEntry, JournalEntryLine, AccountType
from app.models.inventory import InventoryItem, InventoryTransaction, PurchaseMaster
from app.curd.account import create_journal_entry
from app.schemas.account import JournalEntryCreate, JournalEntryLineCreateInEntry

def resolve_initial_stock():
    db = SessionLocal()
    try:
        print("--- Resolving Initial Stock Discrepancy ---")
        
        # 1. Calculate Discrepancy
        
        # A. Ledger Balance for Inventory Asset
        inventory_asset_ledger = db.query(AccountLedger).filter(AccountLedger.name == "Inventory Asset (Stock)").first()
        if not inventory_asset_ledger:
            print("Error: 'Inventory Asset (Stock)' ledger not found.")
            return

        debits = db.query(func.sum(JournalEntryLine.amount))\
            .filter(JournalEntryLine.debit_ledger_id == inventory_asset_ledger.id)\
            .scalar() or 0.0
        credits = db.query(func.sum(JournalEntryLine.amount))\
            .filter(JournalEntryLine.credit_ledger_id == inventory_asset_ledger.id)\
            .scalar() or 0.0
            
        ledger_balance = debits - credits
        print(f"Financial Inventory Value: ₹{ledger_balance:,.2f}")

        # B. Physical Stock Value
        physical_value = db.query(func.sum(InventoryItem.current_stock * InventoryItem.unit_price)).scalar() or 0.0
        print(f"Physical Stock Value:    ₹{physical_value:,.2f}")
        
        difference = physical_value - ledger_balance
        print(f"Difference to Adjust:    ₹{difference:,.2f}")
        
        if abs(difference) < 1.0:
            print("No significant difference found. No adjustment needed.")
            return

        # 2. Find/Create 'Opening Balance Equity' Ledger
        equity_ledger_name = "Opening Balance Equity"
        equity_ledger = db.query(AccountLedger).filter(AccountLedger.name == equity_ledger_name).first()
        
        if not equity_ledger:
            print(f"Creating '{equity_ledger_name}' ledger...")
            # Find Liability Group
            liability_group = db.query(AccountGroup).filter(AccountGroup.name == "Liabilities").first()
            if not liability_group:
                 # Fallback
                 liability_group = db.query(AccountGroup).filter(AccountGroup.account_type == AccountType.LIABILITY).first()
            
            if not liability_group:
                print("Error: Could not find Liabilities group.")
                return

            equity_ledger = AccountLedger(
                name=equity_ledger_name,
                group_id=liability_group.id,
                module="Equity",
                description="To track initial stock and opening balances",
                balance_type="credit"
            )
            db.add(equity_ledger)
            db.commit()
            db.refresh(equity_ledger)
            print(f"Created Ledger ID: {equity_ledger.id}")
        else:
            print(f"Using Existing Ledger ID: {equity_ledger.id}")

        # 3. Create Journal Entry
        print("Creating Journal Entry...")
        
        # Debit Inventory, Credit Equity
        lines = [
            JournalEntryLineCreateInEntry(
                debit_ledger_id=inventory_asset_ledger.id,
                credit_ledger_id=None,
                amount=difference,
                description="Adjustment for Initial/Physical Stock"
            ),
            JournalEntryLineCreateInEntry(
                debit_ledger_id=None,
                credit_ledger_id=equity_ledger.id,
                amount=difference,
                description="Opening Balance for Existing Inventory"
            )
        ]

        entry = JournalEntryCreate(
            entry_date=datetime.utcnow(),
            reference_type="manual_adjustment",
            reference_id=0,
            description="Opening Stock Adjustment",
            notes=f"Auto-correction for initial stock difference of ₹{difference:,.2f}",
            lines=lines
        )
        
        je = create_journal_entry(db, entry, created_by=None) # System created
        print(f"✅ Created Journal Entry #{je.entry_number} (ID: {je.id})")
        print("Discrepancy resolved.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    resolve_initial_stock()
