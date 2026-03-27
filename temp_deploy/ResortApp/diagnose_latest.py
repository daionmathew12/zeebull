import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import PurchaseMaster, LocationStock, InventoryItem, Location

def diagnose_latest():
    db = SessionLocal()
    try:
        print("--- Diagnosing Latest Purchase ---")
        
        purchase = db.query(PurchaseMaster).order_by(PurchaseMaster.id.desc()).first()
        
        if not purchase:
            print("No purchases found.")
            return

        print(f"Purchase ID: {purchase.id}")
        print(f"Status: {purchase.status}")
        print(f"Dest Location ID: {purchase.destination_location_id}") # THIS IS KEY
        
        if purchase.destination_location_id:
            loc = db.query(Location).filter(Location.id == purchase.destination_location_id).first()
            print(f"Location Name: {loc.name if loc else 'Unknown'}")
        else:
            print("WARNING: Destination Location is NULL.")
            
        print("--- Stock Check ---")
        for detail in purchase.details:
            item = db.query(InventoryItem).filter(InventoryItem.id == detail.item_id).first()
            print(f"Item: {item.name} (Global Stock: {item.current_stock})")
            
            if purchase.destination_location_id:
                ls = db.query(LocationStock).filter(
                    LocationStock.location_id == purchase.destination_location_id,
                    LocationStock.item_id == detail.item_id
                ).first()
                print(f"Location Stock: {ls.quantity if ls else 'NO RECORD'}")
            else:
                print("Skipping Location Stock (No Location ID)")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_latest()
