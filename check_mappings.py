from app.utils.auth import get_db
from app.models.inventory import AssetMapping, Location
from sqlalchemy.orm import Session
import os
import sys

# Add the project directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.utils.auth import get_db

db_gen = get_db()
db = next(db_gen)

try:
    mappings = db.query(AssetMapping).all()
    print(f"{'ID':<5} | {'Item ID':<8} | {'Branch ID':<10} | {'Location ID':<12} | {'Active':<7}")
    print("-" * 60)
    for m in mappings:
        print(f"{m.id:<5} | {m.item_id:<8} | {m.branch_id:<10} | {m.location_id:<12} | {m.is_active:<7}")

    print("\nLocations:")
    locations = db.query(Location).all()
    for l in locations:
        print(f"ID: {l.id}, Name: {l.name}, Branch ID: {l.branch_id}")
finally:
    db.close()
