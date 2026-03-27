
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Set up paths
sys.path.append("/var/www/zeebull/ResortApp")
os.chdir("/var/www/zeebull/ResortApp")

from app.database import SessionLocal
from app.models.inventory import Location, LocationStock, InventoryItem, AssetRegistry
from app.models.user import User
from app.schemas.inventory import LocationOut
from sqlalchemy.orm import joinedload
from sqlalchemy import func

def debug_get_locations(branch_id=2):
    db = SessionLocal()
    try:
        # 1. Fetch locations
        loc_query = db.query(Location).options(
            joinedload(Location.parent_location),
            joinedload(Location.branch)
        ).filter(Location.is_active == True)
        
        if branch_id is not None:
            loc_query = loc_query.filter(Location.branch_id == branch_id)
        
        locations = loc_query.offset(0).limit(10000).all()
        print(f"Found {len(locations)} locations.")

        # 2. Consumables
        stock_query = db.query(
            LocationStock.location_id,
            func.count(LocationStock.id),
            func.sum(LocationStock.quantity * InventoryItem.unit_price)
        ).join(InventoryItem, LocationStock.item_id == InventoryItem.id)\
         .filter(LocationStock.quantity > 0)
        
        if branch_id is not None:
            stock_query = stock_query.filter(LocationStock.branch_id == branch_id)
        
        stock_stats = stock_query.group_by(LocationStock.location_id).all()
        stock_map = {loc_id: {"count": c, "value": v or 0} for loc_id, c, v in stock_stats}
        
        # 3. Assets
        asset_query = db.query(
            AssetRegistry.current_location_id,
            func.count(AssetRegistry.id),
            func.sum(InventoryItem.unit_price)
        ).join(InventoryItem, AssetRegistry.item_id == InventoryItem.id)\
         .filter(AssetRegistry.status == 'active')
        
        if branch_id is not None:
            asset_query = asset_query.filter(AssetRegistry.branch_id == branch_id)
        
        asset_stats = asset_query.group_by(AssetRegistry.current_location_id).all()
        asset_map = {loc_id: {"count": c, "value": v or 0} for loc_id, c, v in asset_stats}

        result = []
        for loc in locations:
            parent = loc.parent_location
            s_data = stock_map.get(loc.id, {"count": 0, "value": 0})
            a_data = asset_map.get(loc.id, {"count": 0, "value": 0})
            
            total_items = (s_data["count"] or 0) + (a_data["count"] or 0)
            total_value = float(s_data["value"] or 0) + float(a_data["value"] or 0)
            
            loc_dict = {c.name: getattr(loc, c.name) for c in loc.__table__.columns}
            
            item_data = {
                **loc_dict,
                "parent_location_name": f"{parent.building} - {parent.room_area}" if parent else None,
                "total_items": total_items,
                "total_value": total_value,
                "asset_count": a_data["count"],
                "consumable_count": s_data["count"],
                "branch_id": loc.branch_id,
                "branch_name": loc.branch.name if loc.branch else "Main"
            }
            
            # Validation check
            try:
                # We need to filter the dict to only include fields in LocationOut if we want to test validation
                # But LocationOut includes extra fields in the response usually.
                # Actually, let's just use the Pydantic model directly.
                LocationOut.model_validate(item_data)
            except Exception as ve:
                print(f"Validation Error for location {loc.id} ({loc.name}): {ve}")
                # print(f"Data: {item_data}")
            
            result.append(item_data)
            
        print("Success: Generated results without crash.")
        
    except Exception as e:
        print(f"Crash: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_get_locations(branch_id=2)
    debug_get_locations(branch_id=1)
    debug_get_locations(branch_id=None)
