from app.database import SessionLocal
from app.models.inventory import StockIssue, Location, LocationStock, InventoryTransaction
from sqlalchemy import desc

db = SessionLocal()

print("=== DB DIAGNOSTIC ===")

# 1. Find Room 102
print("\n--- Searching for Room 102 ---")
rooms = db.query(Location).filter(Location.location_type == 'GUEST_ROOM').all()
target_room = None
for r in rooms:
    if "102" in r.name or "102" in (r.room_area or ""):
        print(f"FOUND Room: {r.name} (Area: {r.room_area}, ID: {r.id})")
        target_room = r
        break

if not target_room:
    print("Room 102 NOT FOUND in DB.")
    # List all generic rooms
    print("Available Rooms:", [f"{r.name} ({r.id})" for r in rooms])

# 2. Check Stock Issues
print("\n--- Recent Stock Issues ---")
issues = db.query(StockIssue).order_by(desc(StockIssue.id)).limit(5).all()
if not issues:
    print("No Stock Issues found in DB.")
else:
    for i in issues:
        print(f"Issue {i.issue_number} (ID: {i.id}) - Dest: {i.destination_location_id}")
        for d in i.details:
            print(f"  - Item {d.item_id}: Qty {d.issued_quantity}")

# 3. Check Location Stock for Target Room
if target_room:
    print(f"\n--- Stock for Room {target_room.name} (ID: {target_room.id}) ---")
    stocks = db.query(LocationStock).filter(LocationStock.location_id == target_room.id).all()
    if not stocks:
        print("No stock records found for this room.")
    else:
        for s in stocks:
            print(f"  - Item {s.item_id}: Qty {s.quantity}")

# 4. Check Transactions for Target Room
if target_room:
    print(f"\n--- Transactions for Room {target_room.name} ---")
    # Transactions might store department name or notes?
    # Or we check transactions where 'department' matches room name? 
    # Logic in create_stock_issue: transaction__in.department = dest_location_name
    
    room_name_pattern = f"%{target_room.name}%"
    txns = db.query(InventoryTransaction).filter(
        (InventoryTransaction.department.ilike(room_name_pattern)) |
        (InventoryTransaction.notes.ilike(room_name_pattern))
    ).order_by(desc(InventoryTransaction.id)).limit(5).all()
    
    for t in txns:
        print(f"Txn {t.id}: Type {t.transaction_type}, Qty {t.quantity}, Notes: {t.notes}")

db.close()
