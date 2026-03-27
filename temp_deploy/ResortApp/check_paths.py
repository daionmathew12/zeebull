from app.database import SessionLocal
from app.models.room import Room
from app.models.Package import Package, PackageImage

db = SessionLocal()
print("--- Rooms ---")
for r in db.query(Room).all():
    print(f"ID: {r.id}, Type: {r.type}, Number: {r.number}, Status: {r.status}, Image: {r.image_url}")

print("\n--- Packages ---")
for p in db.query(Package).all():
    imgs = [i.image_url for i in p.images]
    print(f"ID: {p.id}, Title: {p.title}, Status: {p.status}, Images: {imgs}")

db.close()
