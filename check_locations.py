import sys
import os

# Add ResortApp to path to import app
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))

from app.database import SessionLocal
from app.models.inventory import Location
db = SessionLocal()
locs = db.query(Location).all()
for l in locs:
    print(f"ID: {l.id}, Name: {l.name}, Type: {l.location_type}")
db.close()
