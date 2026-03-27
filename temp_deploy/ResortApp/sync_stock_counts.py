from app.database import SessionLocal
from app.models.inventory import InventoryItem, LocationStock

db = SessionLocal()

def sync_stock():
    print("--- Syncing Warehouse Stock with Global Stock ---")
    items = db.query(InventoryItem).filter(InventoryItem.is_active == True).all()
    
    updated_count = 0
    
    for item in items:
        # Get all location stocks
        stocks = db.query(LocationStock).filter(LocationStock.item_id == item.id).all()
        
        # Get all active asset mappings
        from app.models.inventory import AssetMapping
        mappings = db.query(AssetMapping).filter(
            AssetMapping.item_id == item.id,
            AssetMapping.is_active == True
        ).all()
        
        stock_sum = sum(s.quantity for s in stocks)
        mapping_sum = sum(m.quantity or 1.0 for m in mappings)
        
        total_deployed = stock_sum + mapping_sum
        
        # Calculate discrepancy
        # Global Stock should roughly equal Total Deployed? 
        # Actually, LocationStock usually *includes* Warehouse stock.
        # But AssetMapping is *separate* from LocationStock.
        # So yes, Total Deployed = LocationStock (Warehouse + Others) + AssetMappings (Room assignments)
        
        diff = total_deployed - item.current_stock
        
        if diff > 0.001: # Float tolerance
            print(f"Item '{item.name}' (ID {item.id}): Global={item.current_stock}, StockSum={stock_sum}, MapSum={mapping_sum}, Total={total_deployed}, Diff={diff}")
            
            # We assume the discrepancy is due to failure to deduct from Central Warehouse (ID 1)
            # Find Warehouse Stock
            wh_stock = next((s for s in stocks if s.location_id == 1), None)
            
            if wh_stock:
                if wh_stock.quantity >= diff:
                    print(f"  -> Reducing Warehouse Stock by {diff}")
                    wh_stock.quantity -= diff
                    updated_count += 1
                else:
                     print(f"  -> WARNING: Warehouse stock {wh_stock.quantity} is less than diff {diff}. Cannot fully resolve.")
            else:
                 print(f"  -> WARNING: No Warehouse stock entry found.")
                 
    db.commit()
    print(f"--- Completed. Updated {updated_count} items. ---")
    db.close()

if __name__ == "__main__":
    sync_stock()
