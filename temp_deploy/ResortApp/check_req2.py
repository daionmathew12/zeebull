from app.database import SessionLocal
from app.models.service_request import ServiceRequest

db = SessionLocal()
sr = db.query(ServiceRequest).filter(ServiceRequest.id == 2).first()
if sr:
    print(f"ID: {sr.id}, Type: {sr.request_type}, Status: {sr.status}, Room: {sr.room_id}")
else:
    print("SR 2 not found")
db.close()
