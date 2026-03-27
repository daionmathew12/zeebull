from app.database import SessionLocal
from app.models.inventory import InventoryItem, LocationStock

db = SessionLocal()

def fix_light_stock_counts():
    print("--- Correcting 'light' Stock Counts ---")
    
    # User premise: Start = 70.0
    # Calculations:
    # Waste = 1.0 (verified)
    # Assigned = 9.0 (verified)
    #
    # Global Stock Concept:
    # Option A: Global Stock = Total Owned (Start - Waste) = 70 - 1 = 69
    # Option B: Global Stock = Available to Assign (Warehouse) = 70 - 1 - 9 = 60
    #
    # Current behavior of `create_asset_mapping` decrements `item.current_stock`.
    # This implies Option B logic: current_stock represents "Available/Warehouse Stock".
    #
    # BUT, the user likely sees "Stock" in the main table and expects it to be "Total Owned".
    # If the user says "remains 69 but showing 68", they clearly expect Option A.
    # They are seeing 68. 
    #
    # IF `current_stock` is supposed to be "Available", it should be 60.
    # IF `current_stock` is supposed to be "Total Owned", it should be 69.
    #
    # The fact that it is 68 suggests strict confusion.
    # Maybe 1 was "doubly deducted" for waste? 
    # Or maybe one assignment failed to deduct? 
    #
    # Let's align with the SYSTEM DESIGN first.
    # If I look at `LocationStockView.jsx` (frontend), it sums things up?
    # No, the main `Inventory.jsx` shows `item.current_stock`.
    # USUALLY, for Assets, "Stock" means "How many do I have available to give out?".
    # So 60 would be the "correct" number for "Available".
    # But the user says "remains 69". This forces us to treat `current_stock` as Total.
    #
    # However, `create_asset_mapping` REDUCES `current_stock`.
    # So the system is built to treat `current_stock` as "Available".
    #
    # Why is it 68?
    # 70 - 1 (Waste) = 69.
    # 69 - 1 (Maybe one assignment deducted?) = 68.
    # But we have 9 assignments.
    # So 8 assignments DID NOT deduct from `current_stock`?
    #
    # It seems my "sync" scripts might have messed up `current_stock` vs `LocationStock`.
    #
    # Let's reset the numbers to be mathematically consistent.
    # We will assume:
    # 1. We want `item.current_stock` to equal `Warehouse Stock` (Available). 
    #    (If the user wants Total, we'd need to change the frontend to Sum(Available + Assigned)).
    #    But for now, to ensure consistency:
    #    Authorized Stock (Start) = 70
    #    Waste = 1
    #    Assigned = 9
    #    Warehouse Should Be = 60
    #    Global `current_stock` Should Be = 60 (Available)
    #
    # Wait, if I set it to 60, the user will scream "I have 69 lights!".
    # 
    # ALTERNATIVE:
    # `current_stock` = Total Owned (69).
    # `LocationStock(Warehouse)` = Available (60).
    #
    # IF we do this, we must STOP deducting `current_stock` in `create_asset_mapping`.
    # Let's check `create_asset_mapping` again.
    # Step 213: `item.current_stock -= quantity`
    #
    # If I remove that line, `current_stock` stays as Total.
    # And we only deduct from `LocationStock`.
    #
    # This seems to be what the user Wants ("remains 69").
    #
    # So, Plan:
    # 1. Update `create_asset_mapping` to NOT reduce `current_stock`.
    # 2. Update `fix_light_stock_counts` (this script) to set `current_stock` to 69.
    # 3. Ensure `LocationStock` (Warehouse) is 60.
    
    item = db.query(InventoryItem).filter(InventoryItem.name.ilike("light")).first()
    if not item: return

    # 1. Fix Global Stock (Total Owned)
    # User expects 69.
    print(f"Updating Global Stock (Total Owned) from {item.current_stock} to 69.0")
    item.current_stock = 69.0
    
    # 2. Fix Warehouse Stock (Available)
    # Should be 60.
    wh_stock = db.query(LocationStock).filter(
        LocationStock.item_id == item.id, 
        LocationStock.location_id == 1
    ).first()
    
    if wh_stock:
        print(f"Updating Warehouse Stock (Available) from {wh_stock.quantity} to 60.0")
        wh_stock.quantity = 60.0
    
    # 3. Double check other items? 
    # The user complained about "light". Let's fix "light" specifically first.
    
    db.commit()
    print("--- Fix Complete ---")

if __name__ == "__main__":
    fix_light_stock_counts()
