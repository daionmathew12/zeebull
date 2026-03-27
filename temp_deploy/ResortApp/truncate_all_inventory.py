from app.database import SessionLocal
from sqlalchemy import text
import sys

def truncate_all():
    db = SessionLocal()
    try:
        print("--- TRUNCATING ALL INVENTORY TABLES ---")
        
        # 1. Reset room inventory location IDs (Foreign Keys)
        print("Resetting room inventory links...")
        db.execute(text("UPDATE rooms SET inventory_location_id = NULL"))
        
        # 2. Delete/Truncate all
        # Order doesn't strictly matter with CASCADE but let's be careful or use TRUNCATE CASCADE
        sql = """
        TRUNCATE 
            laundry_logs, 
            waste_logs, 
            stock_issue_details, 
            stock_issues, 
            stock_requisition_details, 
            stock_requisitions, 
            inventory_transactions, 
            purchase_details, 
            purchase_masters, 
            asset_mappings, 
            asset_registry, 
            recipe_ingredients, 
            recipes, 
            location_stocks, 
            service_inventory_items, 
            inventory_items, 
            inventory_categories, 
            vendors
        CASCADE;
        """
        print("Executing TRUNCATE CASCADE...")
        db.execute(text(sql))
        
        # 3. Handle Locations
        print("Deleting non-guest locations...")
        db.execute(text("DELETE FROM locations WHERE location_type NOT IN ('Guest Room', 'GUEST_ROOM')"))
        
        db.commit()
        print("--- ALL INVENTORY DATA CLEARED ---")
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    truncate_all()
