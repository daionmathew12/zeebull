import os
import sys
from dotenv import load_dotenv

# Add the ResortApp directory to sys.path
sys.path.append('.')

# Load .env from the current directory
load_dotenv()

try:
    from app.database import SessionLocal
    from app.models.room import Room
    from app.models.inventory import LocationStock, AssetMapping, AssetRegistry, Location
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

db = SessionLocal()
loc_id = 6# Room 101
print(f"--- DIAGNOSTICS FOR LOCATION {loc_id} ---")

stocks = db.query(LocationStock).filter(LocationStock.location_id == loc_id).all()
print(f'LocationStock count: {len(stocks)}')
for s in stocks:
    print(f'  - Item: {s.item.name if s.item else "Unknown"} (ID: {s.item_id}), Qty: {s.quantity}')

mappings = db.query(AssetMapping).filter(AssetMapping.location_id == loc_id).all()
print(f'AssetMapping count: {len(mappings)}')
for m in mappings:
    print(f'  - Item: {m.item.name if m.item else "Unknown"} (ID: {m.item_id}), Qty: {m.quantity}, IsActive: {m.is_active}')

registry = db.query(AssetRegistry).filter(AssetRegistry.current_location_id == loc_id).all()
print(f'AssetRegistry count: {len(registry)}')
for a in registry:
    print(f'  - Item: {a.item.name if a.item else "Unknown"} (ID: {a.item_id}), AssetTag: {a.asset_tag_id}, Status: {a.status}')

db.close()
print("--- END DIAGNOSTICS ---")
