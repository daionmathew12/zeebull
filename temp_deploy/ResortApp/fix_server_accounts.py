import sqlalchemy
from sqlalchemy import create_engine, text
import os

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"
# On server, user is postgres mostly, db is orchid_resort. But here running LOCALLY?
# No, run on SERVER.

def fix_accounts():
    # Detect environment
    if os.path.exists("/var/www/inventory/ResortApp"):
        # Server environment likely
        db_url = "postgresql+psycopg2://orchid_user:orchid_pass@localhost/orchid_resort"
        # Or checking env file...
        # Let's assume user postgres locally for simple script
        db_url = "postgresql+psycopg2://postgres@localhost/orchid_resort"
    else:
        print("Not on server or unknown path")
        return

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("Connected to DB.")
            
            # 1. Update Room Revenue
            result = conn.execute(text("UPDATE account_ledgers SET name='Room Revenue (Taxable)' WHERE name='Room Revenue'"))
            print(f"Room Revenue updated: {result.rowcount}")

            # 2. Update Food Revenue
            result = conn.execute(text("UPDATE account_ledgers SET name='Food Revenue (Taxable)' WHERE name='Food & Beverage Revenue'"))
            print(f"Food Revenue updated: {result.rowcount}")

            # 3. Update Service Revenue
            result = conn.execute(text("UPDATE account_ledgers SET name='Service Revenue (Taxable)' WHERE name='Service Revenue'"))
            print(f"Service Revenue updated: {result.rowcount}")

            # 4. Check/Insert Package Revenue (Assuming Group ID 1 is Revenue Accounts)
            # Find group ID first
            result = conn.execute(text("SELECT id FROM account_groups WHERE name='Revenue Accounts'"))
            group = result.fetchone()
            if group:
                group_id = group[0]
                # Check exist
                exists = conn.execute(text("SELECT 1 FROM account_ledgers WHERE name='Package Revenue (Taxable)'")).fetchone()
                if not exists:
                    conn.execute(text(f"INSERT INTO account_ledgers (name, group_id, module, is_active, balance_type) VALUES ('Package Revenue (Taxable)', {group_id}, 'Booking', true, 'credit')"))
                    print("Package Revenue (Taxable) inserted.")
                else:
                    print("Package Revenue (Taxable) already exists.")
            
            # 5. Check GST Ledgers
            gst_ledgers = ["Output CGST", "Output SGST", "Output IGST"]
            # Find Duties & Taxes group
            result = conn.execute(text("SELECT id FROM account_groups WHERE name='Duties & Taxes'"))
            tax_group = result.fetchone()
            if tax_group:
                tax_group_id = tax_group[0]
                for ledger in gst_ledgers:
                     exists = conn.execute(text(f"SELECT 1 FROM account_ledgers WHERE name='{ledger}'")).fetchone()
                     if not exists:
                         conn.execute(text(f"INSERT INTO account_ledgers (name, group_id, module, is_active, balance_type, tax_type) VALUES ('{ledger}', {tax_group_id}, 'Tax', true, 'credit', 'Output')"))
                         print(f"{ledger} inserted.")
                     else:
                        print(f"{ledger} exists.")

            conn.commit()
            print("Account updates committed.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_accounts()
