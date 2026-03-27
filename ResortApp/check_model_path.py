
import app.models.inventory
import os

print(f"app.models.inventory file: {os.path.abspath(app.models.inventory.__file__)}")

from app.models.inventory import InventoryItem
from sqlalchemy import Column

print(f"InventoryItem columns: {[c.name for c in InventoryItem.__table__.columns]}")
if 'branch_id' in [c.name for c in InventoryItem.__table__.columns]:
    print("branch_id FOUND in InventoryItem model!")
else:
    print("branch_id NOT found in InventoryItem model.")
