
import os
import sys
from sqlalchemy import inspect

# Add project root to path
sys.path.append(os.getcwd())

from app.models.inventory import InventoryItem

def inspect_mapper():
    mapper = inspect(InventoryItem)
    print(f"Mapper for InventoryItem table: {mapper.local_table.name}")
    print(f"Columns in local_table: {[c.name for c in mapper.local_table.columns]}")
    
    print("\nAttributes in mapper:")
    for attr in mapper.all_orm_descriptors:
        print(f" - {attr}")
        
    if 'branch_id' in [c.name for c in mapper.local_table.columns]:
        print("\n!!! branch_id FOUND in Mapper's local_table.columns !!!")
        # Let's see where it's defined
        col = mapper.local_table.columns['branch_id']
        print(f"Column properties: {col.__dict__}")
    else:
        print("\nbranch_id NOT found in Mapper's local_table.columns.")

if __name__ == "__main__":
    inspect_mapper()
