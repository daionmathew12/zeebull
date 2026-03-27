from app.database import SessionLocal
from app.models.inventory import LocationStock, AssetMapping, InventoryItem

def fix_stock():
    db = SessionLocal()
    loc_id = 5 # Room 102
    item_id = 3 # LED Bulb
    
    stock = db.query(LocationStock).filter(LocationStock.location_id == loc_id, LocationStock.item_id == item_id).first()
    if stock:
        print(f"Updating stock from {stock.quantity} to 2.0")
        stock.quantity = 2.0
        db.commit()
    else:
        print("Stock record not found, creating one...")
        new_stock = LocationStock(location_id=loc_id, item_id=item_id, quantity=2.0)
        db.add(new_stock)
        db.commit()
    db.close()

if __name__ == "__main__":
    fix_stock()
