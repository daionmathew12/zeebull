"""
Check account_groups branch_id and fix visibility.
Groups seeded without branch_id (NULL) won't show for any specific branch.
Fix: make NULL branch_id groups visible to all branches, OR update get_account_groups
to also return NULL branch_id groups.
"""
import sys
sys.path.insert(0, r'c:\releasing\New Orchid\ResortApp')

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # Check current state
    result = db.execute(text("SELECT id, name, branch_id FROM account_groups ORDER BY id LIMIT 20")).fetchall()
    print("=== Current Account Groups ===")
    for row in result:
        print(f"  ID={row[0]}, Name={row[1][:30]}, branch_id={row[2]}")

    # Check branches
    branches = db.execute(text("SELECT id, name FROM branches")).fetchall()
    print(f"\n=== Branches ===")
    for b in branches:
        print(f"  ID={b[0]}, Name={b[1]}")

    # Check ledgers
    ledger_count = db.execute(text("SELECT COUNT(*) FROM account_ledgers")).scalar()
    print(f"\n=== Account Ledgers: {ledger_count} total ===")

    null_groups = db.execute(text("SELECT COUNT(*) FROM account_groups WHERE branch_id IS NULL")).scalar()
    print(f"Groups with NULL branch_id: {null_groups}")

    print("\n✅ The account groups have NULL branch_id (seeded without branch).")
    print("Fix needed: Update get_account_groups to include NULL branch_id groups (global groups).")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
