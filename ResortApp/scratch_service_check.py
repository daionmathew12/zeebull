from app.database import SessionLocal
from app.models.service_request import ServiceRequest
from app.models.service import AssignedService
from app.models.room import Room

db = SessionLocal()
room_101 = db.query(Room).filter(Room.number == "101").first()
print(f"Room 101 ID: {room_101.id}")

srs = db.query(ServiceRequest).filter(ServiceRequest.room_id == room_101.id).all()
print(f"Service Requests for Room 101: {len(srs)}")
for sr in srs:
    print(f"  - SR ID: {sr.id}, Type: {sr.request_type}, Status: {sr.status}, Description: {sr.description}")

assigned = db.query(AssignedService).filter(AssignedService.room_id == room_101.id).all()
print(f"Assigned Services for Room 101: {len(assigned)}")
for a in assigned:
    print(f"  - Assigned ID: {a.id}, Status: {a.status}, Desc: {a.service.name if a.service else 'none'}")
