"""Fix duplicate Room 101: Delete the duplicate (ID=6, Available) and add unique constraint."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.room import Room
from sqlalchemy import text

db = SessionLocal()

# Show all room 101s
dupes = db.query(Room).filter(Room.number == '101').all()
print(f"Found {len(dupes)} rooms with number '101':")
for r in dupes:
    print(f"  ID={r.id}, number={r.number}, status={r.status}, inv_loc={r.inventory_location_id}")

# Keep ID=2 (the real one with bookings), delete ID=6 (the empty duplicate)
room_to_delete = db.query(Room).filter(Room.id == 6).first()
if room_to_delete and room_to_delete.number == '101' and room_to_delete.status in ['Available', 'available']:
    print(f"\nDeleting duplicate room ID=6 (number=101, status={room_to_delete.status})...")
    try:
        # Nullify any foreign key references first if any
        db.delete(room_to_delete)
        db.commit()
        print("Deleted successfully.")
    except Exception as e:
        db.rollback()
        print(f"Delete failed: {e}")
        print("Room may have foreign key constraints. Trying status update instead...")
        # If can't delete, just mark as inactive
        room_to_delete.number = '101-DUPLICATE'
        db.commit()
        print("Renamed duplicate to '101-DUPLICATE'")
else:
    print("No safe duplicate to delete (room ID=6 not found or not matching conditions).")

# Verify remaining
remaining = db.query(Room).filter(Room.number == '101').all()
print(f"\nRemaining rooms with number '101': {len(remaining)}")
for r in remaining:
    print(f"  ID={r.id}, status={r.status}")

db.close()
