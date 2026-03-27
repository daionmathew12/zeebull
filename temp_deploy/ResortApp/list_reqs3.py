from app.database import SessionLocal
from app.models.service import AssignedService

db = SessionLocal()
srs = db.query(AssignedService).all()
for sr in srs:
    print(f"ID: {sr.id} (Returned as {sr.id + 2000000}), Status: {sr.status}, Room: {sr.room_id}")
db.close()
