import os
from sqlalchemy import text
from app.database import SessionLocal

def clear_inventory():
    db = SessionLocal()
    try:
        print("--- Clearing ALL Inventory Data (Full Wipe) ---")
        
        # 1. Clear Transactional / Child Tables first
        tables_to_clear = [
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
            "location_stocks",
            "recipe_ingredients",
            "recipes",
            "service_inventory_items"
        ]
        
        for table in tables_to_clear:
            print(f"Clearing {table}...")
            try:
                db.execute(text(f"DELETE FROM {table}"))
            except Exception as e:
                print(f"Skipping {table} (not found or error: {e})")
        
        # 2. Clear Master Data
        print("Clearing inventory_items...")
        db.execute(text("DELETE FROM inventory_items"))
        
        print("Clearing inventory_categories...")
        db.execute(text("DELETE FROM inventory_categories"))
        
        print("Clearing vendors...")
        db.execute(text("DELETE FROM vendors"))
        
        # 3. Clear Locations (but keep guest rooms)
        print("Clearing inventory locations (keeping guest rooms)...")
        db.execute(text("DELETE FROM locations WHERE location_type != 'Guest Room' AND location_type != 'GUEST_ROOM'"))
        
        # 4. Optional: Reset inventory_location_id in Room table
        print("Resetting room inventory links...")
        db.execute(text("UPDATE rooms SET inventory_location_id = NULL"))
        
        db.commit()
        print("\nSUCCESS: All inventory data wiped from server!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_inventory()
