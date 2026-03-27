from app.database import SessionLocal
from app.models.service_request import ServiceRequest

db = SessionLocal()
srs = db.query(ServiceRequest).all()
for sr in srs:
    print(f"ID: {sr.id}, Type: {sr.request_type}, Status: {sr.status}, Room: {sr.room_id}")
db.close()
