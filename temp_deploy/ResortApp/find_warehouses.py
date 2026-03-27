from app.database import SessionLocal
from app.models.inventory import Location
from sqlalchemy import text

db = SessionLocal()

print("--- Searching for Warehouses ---")
# Fallback to simple query logic or raw SQL if ILIKE issues (though postgres supports it, maybe ORM mapping issue?)
locs = db.query(Location).all()
for l in locs:
    if "WAREHOUSE" in str(l.location_type).upper():
        print(f"ID: {l.id}, Name: {l.name}, Code: {l.location_code}")

db.close()
