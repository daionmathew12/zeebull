import os
import sys
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
from app.database import SessionLocal
import sqlalchemy as sa

def debug_db():
    db = SessionLocal()
    try:
        # Check inventory_items
        res = db.execute(sa.text("SELECT id, name, branch_id, current_stock FROM inventory_items")).fetchall()
        print("--- ALL INVENTORY ITEMS ---")
        for row in res:
            print(row)
            
        # Check location_stock
        res = db.execute(sa.text("SELECT id, location_id, item_id, quantity, branch_id FROM location_stocks")).fetchall()
        print("\n--- ALL LOCATION STOCK ---")
        for row in res:
            print(row)
            
        # Check inter_branch_transfers
        res = db.execute(sa.text("SELECT id, transfer_number, item_id, status, source_branch_id, destination_branch_id FROM inter_branch_transfers")).fetchall()
        print("\n--- ALL TRANSFERS ---")
        for row in res:
            print(row)
            
    finally:
        db.close()

if __name__ == "__main__":
    debug_db()
