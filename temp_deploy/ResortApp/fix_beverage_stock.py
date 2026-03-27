"""
Fix Coca Cola and Mineral Water global stock
by summing up all location stocks
"""
from app.database import SessionLocal
from app.models.inventory import InventoryItem, LocationStock
from sqlalchemy import func

def fix_beverage_stock():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("FIXING COCA COLA AND MINERAL WATER STOCK")
        print("=" * 70)
        
        # Find Coca Cola
        coca_cola = db.query(InventoryItem).filter(
            InventoryItem.name.ilike("%coca%cola%")
        ).first()
        
        if coca_cola:
            # Sum all location stocks
            total_stock = db.query(func.sum(LocationStock.quantity)).filter(
                LocationStock.item_id == coca_cola.id
            ).scalar() or 0
            
            print(f"\n🥤 Coca Cola 750ml:")
            print(f"   Current Global Stock: {coca_cola.current_stock}")
            print(f"   Sum of Location Stocks: {total_stock}")
            print(f"   Difference: {total_stock - coca_cola.current_stock}")
            
            # Update global stock
            coca_cola.current_stock = total_stock
            print(f"\n   ✅ Updated global stock to: {total_stock}")
        
        # Find Mineral Water
        mineral_water = db.query(InventoryItem).filter(
            InventoryItem.name.ilike("%mineral%water%")
        ).first()
        
        if mineral_water:
            # Sum all location stocks
            total_stock = db.query(func.sum(LocationStock.quantity)).filter(
                LocationStock.item_id == mineral_water.id
            ).scalar() or 0
            
            print(f"\n💧 Mineral Water 1L:")
            print(f"   Current Global Stock: {mineral_water.current_stock}")
            print(f"   Sum of Location Stocks: {total_stock}")
            print(f"   Difference: {total_stock - mineral_water.current_stock}")
            
            # Update global stock
            mineral_water.current_stock = total_stock
            print(f"\n   ✅ Updated global stock to: {total_stock}")
        
        # Commit changes
        db.commit()
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Stock levels fixed.")
        print("=" * 70)
        print("\nRefresh the inventory page to see the updated stock levels.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_beverage_stock()
