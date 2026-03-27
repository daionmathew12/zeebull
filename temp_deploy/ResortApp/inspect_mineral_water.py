from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction

db = SessionLocal()
item = db.query(InventoryItem).filter(InventoryItem.name.ilike('%Mineral Water%')).first()
if item:
    print(f"Item: {item.name}, ID: {item.id}, Current Stock: {item.current_stock}")
    txns = db.query(InventoryTransaction).filter(InventoryTransaction.item_id == item.id).all()
    for t in txns:
        print(f"  ID: {t.id}, Type: {t.transaction_type}, Qty: {t.quantity}, Notes: {t.notes}, Ref: {t.reference_number}")
else:
    print("Item not found")
db.close()
