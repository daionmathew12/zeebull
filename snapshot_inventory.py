import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("LOCATIONS:")
    locs = conn.execute(text("SELECT id, name FROM locations")).fetchall()
    for l in locs: print(l)
    
    print("\nASSET_MAPPINGS (ALL):")
    mappings = conn.execute(text("SELECT id, item_id, location_id, quantity, serial_number, branch_id, is_active FROM asset_mappings")).fetchall()
    for m in mappings: print(m)
    
    print("\nLOCATION_STOCKS (ALL):")
    stocks = conn.execute(text("SELECT id, location_id, item_id, quantity, branch_id FROM location_stocks")).fetchall()
    for s in stocks: print(s)
    
    print("\nASSET_REGISTRY:")
    registry = conn.execute(text("SELECT id, item_id, serial_number, branch_id FROM asset_registry")).fetchall()
    for r in registry: print(r)
    
    print("\nITEMS:")
    items = conn.execute(text("SELECT id, name FROM inventory_items")).fetchall()
    for i in items: print(i)
