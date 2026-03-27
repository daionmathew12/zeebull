
from app.database import SessionLocal
from app.models.inventory import LocationStock, Location, InventoryItem

def inspect_duplicates():
    db = SessionLocal()
    try:
        # Find duplicate items in location_stocks for Room 101 (or any room)
        print("Checking duplicate LocationStock entries...")
        
        # Get Room 101 location ID
        room_loc = db.query(Location).filter(Location.name.ilike("%Room 101%")).first()
        if not room_loc:
             print("Room 101 Location not found")
             return

        print(f"Room 101 Location ID: {room_loc.id}")

        stocks = db.query(LocationStock).filter(LocationStock.location_id == room_loc.id).all()
        
        seen = {}
        duplicates = []
        for s in stocks:
            item = db.query(InventoryItem).get(s.item_id)
            item_name = item.name if item else f"Item {s.item_id}"
            
            key = (s.location_id, s.item_id)
            if key in seen:
                duplicates.append((s, seen[key], item_name))
            else:
                seen[key] = s
            
            print(f"ID: {s.id}, Loc: {s.location_id}, Item: {s.item_id} ({item_name}), Qty: {s.quantity}")

        if duplicates:
            print("\nDUPLICATES FOUND:")
            for dup, original, name in duplicates:
                print(f"Duplicate ID: {dup.id} matches Original ID: {original.id} for Item: {name}")
                
            # Uncomment to fix
            # for dup, _, _ in duplicates:
            #     db.delete(dup)
            # db.commit()
            # print("Deleted duplicates.")
        else:
            print("\nNo duplicates found in LocationStock table.")

    finally:
        db.close()

if __name__ == "__main__":
    inspect_duplicates()
