
from app.utils.auth import get_db
from app.models.service import AssignedService
from sqlalchemy import desc

db = next(get_db())

print("--- RECENT ASSIGNED SERVICES ---")
services = db.query(AssignedService).order_by(desc(AssignedService.id)).limit(5).all()
for s in services:
    print(f"ID: {s.id}, Svc: {s.service_id}, Room: {s.room_id}, Status: {s.status}, Branch: {s.branch_id}")
