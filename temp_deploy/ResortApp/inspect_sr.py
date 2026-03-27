from app.database import SessionLocal
from app.models.service_request import ServiceRequest

db = SessionLocal()
reqs = db.query(ServiceRequest).all()
for r in reqs:
    print(f"ID: {r.id}, Status: {r.status}, Emp: {r.employee_id}, Type: {r.request_type}")
db.close()
