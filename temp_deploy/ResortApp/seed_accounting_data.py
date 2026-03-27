"""
Seed script to populate Chart of Accounts using ORM
"""
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add the parent directory to sys.path to ensure modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.account import AccountGroup, AccountLedger, AccountType

def seed_data():
    print("============================================================")
    print("Seeding Chart of Accounts (ORM)")
    print("============================================================")

    db: Session = SessionLocal()

    try:
        # 1. Create Account Groups
        groups_data = [
            {"name": "Sales Accounts", "account_type": AccountType.REVENUE, "description": "Income from business operations"},
            {"name": "Duties & Taxes", "account_type": AccountType.LIABILITY, "description": "Tax liabilities and assets"},
            {"name": "Current Assets", "account_type": AccountType.ASSET, "description": "Assets expected to be sold or used within a year"},
            {"name": "Direct Expenses", "account_type": AccountType.EXPENSE, "description": "Expenses directly related to production"},
            {"name": "Indirect Expenses", "account_type": AccountType.EXPENSE, "description": "Operating expenses"},
            {"name": "Current Liabilities", "account_type": AccountType.LIABILITY, "description": "Short-term financial obligations"},
            {"name": "Bank Accounts", "account_type": AccountType.ASSET, "description": "Bank account balances"},
            {"name": "Cash-in-hand", "account_type": AccountType.ASSET, "description": "Cash holdings"},
            {"name": "Purchase Accounts", "account_type": AccountType.EXPENSE, "description": "Cost of goods purchasing"},
        ]

        print("\nStep 1: Account Groups...")
        group_map = {} # name -> id
        
        for g in groups_data:
            group = db.query(AccountGroup).filter(AccountGroup.name == g["name"]).first()
            if group:
                print(f"  - Group '{g['name']}' already exists (ID: {group.id})")
            else:
                group = AccountGroup(
                    name=g["name"],
                    account_type=g["account_type"],
                    description=g["description"]
                )
                db.add(group)
                db.flush()
                print(f"  + Created Group '{g['name']}' (ID: {group.id})")
            
            group_map[g["name"]] = group.id

        # 2. Create Account Ledgers
        ledgers_data = [
            ("Room Revenue (Taxable)", "Sales Accounts", "Booking", "credit"),
            ("Food Revenue (Taxable)", "Sales Accounts", "Food", "credit"),
            ("Service Revenue (Taxable)", "Sales Accounts", "Service", "credit"),
            ("Package Revenue (Taxable)", "Sales Accounts", "Booking", "credit"),
            ("Service Revenue", "Sales Accounts", "Service", "credit"),
            ("Package Revenue", "Sales Accounts", "Booking", "credit"),
            ("Output CGST", "Duties & Taxes", "Tax", "credit"),
            ("Output SGST", "Duties & Taxes", "Tax", "credit"),
            ("Output IGST", "Duties & Taxes", "Tax", "credit"),
            ("Input CGST", "Duties & Taxes", "Tax", "debit"),
            ("Input SGST", "Duties & Taxes", "Tax", "debit"),
            ("Input IGST", "Duties & Taxes", "Tax", "debit"),
            ("Accounts Receivable (Guest)", "Current Assets", "Booking", "debit"),
            ("Inventory Asset (Stock)", "Current Assets", "Inventory", "debit"),
            ("Cash in Hand", "Cash-in-hand", "Asset", "debit"),
            ("Bank Account (HDFC)", "Bank Accounts", "Asset", "debit"),
            ("Bank Account (SBI)", "Bank Accounts", "Asset", "debit"),
            ("Accounts Payable (Vendor)", "Current Liabilities", "Purchase", "credit"),
            ("Advance from Customers", "Current Liabilities", "Liability", "credit"),
            ("Cost of Goods Sold (COGS)", "Direct Expenses", "Purchase", "debit"),
            ("Consumables Expense", "Direct Expenses", "Purchase", "debit"),
            ("Discount Allowed", "Indirect Expenses", "Expense", "debit"),
            ("General Expense", "Indirect Expenses", "Expense", "debit"),
            ("Housekeeping Expense", "Indirect Expenses", "Expense", "debit"),
            ("Maintenance Expense", "Indirect Expenses", "Expense", "debit"),
            ("Kitchen Expense", "Direct Expenses", "Expense", "debit"),
        ]

        print("\nStep 2: Account Ledgers...")
        
        for name, group_name, module, balance_type in ledgers_data:
            group_id = group_map.get(group_name)
            if not group_id:
                print(f"  ! Error: Group '{group_name}' not found for ledger '{name}'")
                continue
                
            ledger = db.query(AccountLedger).filter(AccountLedger.name == name).first()
            if ledger:
                print(f"  - Ledger '{name}' already exists")
            else:
                ledger = AccountLedger(
                    name=name,
                    group_id=group_id,
                    module=module,
                    balance_type=balance_type,
                    is_active=True
                )
                db.add(ledger)
                print(f"  + Created Ledger '{name}'")

        db.commit()
        print("\n============================================================")
        print("✅ Chart of Accounts seeding completed successfully!")
        print("============================================================")

    except Exception as e:
        db.rollback()
        print(f"❌ An error occurred during seeding: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
