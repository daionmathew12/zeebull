from app.database import SessionLocal
from app.models.room import Room
import json

db = SessionLocal()
rooms = db.query(Room).all()

for r in rooms:
    print(f"Room {r.number}:")
    print(f"  image_url: {r.image_url}")
    print(f"  extra_images: {r.extra_images}")
    print("-" * 20)

db.close()
