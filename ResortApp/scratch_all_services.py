from app.database import SessionLocal
from app.models.service_request import ServiceRequest
from app.models.service import AssignedService

db = SessionLocal()

srs = db.query(ServiceRequest).all()
print(f"Total Service Requests: {len(srs)}")
for sr in srs:
    print(f"  - SR ID: {sr.id}, Room: {sr.room_id}, Type: {sr.request_type}, Status: {sr.status}")

assigned = db.query(AssignedService).all()
print(f"Total Assigned Services: {len(assigned)}")
for a in assigned:
    print(f"  - Assigned ID: {a.id}, Room: {a.room_id}, Status: {a.status}, Desc: {a.service.name if a.service else 'none'}")
