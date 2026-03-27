
import os
import sys
from sqlalchemy import create_engine, MetaData

# Add project root to path
sys.path.append(os.getcwd())

from app.models.inventory import InventoryItem
from app.database import Base

def check_all_tables_metadata():
    metadata = Base.metadata
    print(f"Total tables in metadata: {len(metadata.tables)}")
    
    for table_name, table in metadata.tables.items():
        if 'branch_id' in [c.name for c in table.columns]:
            print(f"Table '{table_name}' HAS branch_id")
            if table_name == 'inventory_items':
                print("!!! WARNING: Metadata thinks inventory_items HAS branch_id !!!")
        
    # Check InventoryItem specifically
    if 'branch_id' in [c.name for c in InventoryItem.__table__.columns]:
         print("\nInventoryItem.__table__ HAS branch_id")
    else:
         print("\nInventoryItem.__table__ does NOT have branch_id")

if __name__ == "__main__":
    check_all_tables_metadata()
