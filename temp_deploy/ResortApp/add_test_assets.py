from app.database import SessionLocal
from sqlalchemy import text
from datetime import datetime

db = SessionLocal()

try:
    # Find Room 101 location
    location = db.execute(text("SELECT id FROM locations WHERE room_area = '101' OR name LIKE '%101%' LIMIT 1")).fetchone()
    
    if not location:
        print("Room 101 location not found in database")
        db.close()
        exit()
    
    loc_id = location[0]
    print(f"Found Room 101 location ID: {loc_id}")
    
    # Find fixed asset items
    items = db.execute(text("SELECT id, name FROM inventory_items WHERE is_asset_fixed = true LIMIT 5")).fetchall()
    
    if not items:
        print("No fixed asset items found in inventory")
        db.close()
        exit()
    
    print(f"Found {len(items)} fixed asset items")
    
    # Add assets to Room 101
    for idx, item in enumerate(items):
        asset_tag = f'AST-101-{idx+1:03d}'
        serial = f'SN{datetime.now().year}{idx+1:04d}'
        
        # Check if asset already exists
        existing = db.execute(text(f"SELECT id FROM asset_registry WHERE asset_tag_id = '{asset_tag}'")).fetchone()
        
        if not existing:
            db.execute(text(
                f"""INSERT INTO asset_registry 
                (asset_tag_id, item_id, serial_number, current_location_id, status, created_at, updated_at) 
                VALUES ('{asset_tag}', {item[0]}, '{serial}', {loc_id}, 'active', NOW(), NOW())"""
            ))
            print(f"✓ Added: {asset_tag} - {item[1]} (Serial: {serial})")
        else:
            print(f"  Skipped: {asset_tag} - already exists")
    
    db.commit()
    print("\n✓ Assets successfully added to Room 101!")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
