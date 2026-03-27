from app.database import SessionLocal
from sqlalchemy import text
import sys

def full_wipe():
    db = SessionLocal()
    try:
        print("--- STARTING FULL INVENTORY WIPE ---")
        
        # Order matters for Foreign Keys
        tables = [
            "laundry_logs",
            "waste_logs",
            "stock_issue_details",
            "stock_issues",
            "stock_requisition_details",
            "stock_requisitions",
            "inventory_transactions",
            "purchase_details",
            "purchase_masters",
            "asset_mappings",
            "asset_registry",
            "recipe_ingredients",
            "recipes",
            "location_stocks",
            "service_inventory_items",
            "inventory_items",
            "inventory_categories",
            "vendors"
        ]
        
        for table in tables:
            print(f"Clearing table: {table}")
            try:
                db.execute(text(f"DELETE FROM {table}"))
            except Exception as e:
                print(f"  Note: {table} could not be cleared (may not exist or {e})")
        
        print("Clearing non-guest-room locations...")
        db.execute(text("DELETE FROM locations WHERE location_type NOT IN ('Guest Room', 'GUEST_ROOM')"))
        
        print("Resetting room inventory links...")
        db.execute(text("UPDATE rooms SET inventory_location_id = NULL"))
        
        db.commit()
        print("--- FULL WIPE COMPLETED SUCCESSFULLY ---")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    full_wipe()
