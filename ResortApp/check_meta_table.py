
import os
import sys
from sqlalchemy import inspect

# Add project root to path
sys.path.append(os.getcwd())

from app.models.inventory import InventoryItem
from app.database import Base

def check_metadata_vs_table():
    print(f"InventoryItem.__table__.columns: {[c.name for c in InventoryItem.__table__.columns]}")
    
    table = Base.metadata.tables.get('inventory_items')
    if table is not None:
        print(f"Base.metadata.tables['inventory_items'].columns: {[c.name for c in table.columns]}")
    else:
        print("inventory_items table NOT found in metadata.tables")
        
if __name__ == "__main__":
    check_metadata_vs_table()
