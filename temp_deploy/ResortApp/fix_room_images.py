"""
Fix room images:
1. Update image_url for all rooms to use the one image that exists locally
2. This makes the user-end show room images correctly
"""
import glob
import os
from app.database import SessionLocal
from app.models.room import Room

db = SessionLocal()

# Find all existing room image files
rooms_dir = "uploads/rooms"
files = os.listdir(rooms_dir)
print(f"Existing room image files: {files}")

if files:
    # Use the first available image for all rooms
    image_file = files[0]
    image_url = f"/uploads/rooms/{image_file}"
    print(f"\nWill set image_url to: {image_url} for rooms without images")
    
    rooms = db.query(Room).all()
    updated = 0
    for room in rooms:
        if not room.image_url:
            room.image_url = image_url
            updated += 1
            print(f"  Updated room {room.id} ({room.type} #{room.number}): {image_url}")
        else:
            print(f"  Room {room.id} ({room.type} #{room.number}) already has image: {room.image_url}")
    
    db.commit()
    print(f"\nUpdated {updated} rooms with image URL")
else:
    print("No room image files found in uploads/rooms/")

db.close()
