import sys, os
sys.path.insert(0, '/var/www/inventory/ResortApp')
from app.database import SessionLocal
from app.models.inventory import InventoryTransaction, InventoryItem

db = SessionLocal()

# Find bed sheet item
items = db.query(InventoryItem).filter(InventoryItem.name.ilike('%bed%')).all()
for i in items:
    print(f"ITEM_ID:{i.id} NAME:{i.name} CAT:{i.category_id}")

print("===")

# All transactions
all_txns = db.query(InventoryTransaction).order_by(InventoryTransaction.created_at.desc()).all()
for t in all_txns:
    item = db.query(InventoryItem).filter(InventoryItem.id == t.item_id).first()
    iname = item.name if item else 'UNKNOWN'
    print(f"ID:{t.id}|TYPE:{t.transaction_type}|ITEM:{iname}|REF:{t.reference_number}|QTY:{t.quantity}|SRC:{t.source_location_id}|DST:{t.destination_location_id}")

db.close()
