from app.database import SessionLocal
from app.api.inventory import get_location_items
from app.models.room import Room

def debug_room_103():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == '103').first()
    if not room:
        print("Room 103 not found")
        return
    
    response = get_location_items(room.inventory_location_id, db, None)
    items_list = response.get("items", [])
    print(f"--- FINAL ITEMS LIST (Count: {len(items_list)}) ---")
    for v in items_list:
        print(f"{v['item_name']:30} | Qty: {v['current_stock']} | Source: {v.get('source', 'Unknown')}")
    db.close()

if __name__ == "__main__":
    debug_room_103()
