
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.database import Base
# Import ALL models that use Base
import app.models.inventory
import app.models.user
import app.models.branch
import app.models.service
import app.models.room

def find_column_in_all_tables():
    metadata = Base.metadata
    for table_name, table in metadata.tables.items():
        if 'branch_id' in [c.name for c in table.columns]:
            print(f"Table '{table_name}' has 'branch_id'")
        
        # Check for ANY foreign keys pointing to branches.id on inventory_items
        if table_name == 'inventory_items':
            print(f"Columns in 'inventory_items': {[c.name for c in table.columns]}")
            for fk in table.foreign_keys:
                print(f" - FK: {fk.target_fullname} on column {fk.parent.name}")

if __name__ == "__main__":
    find_column_in_all_tables()
