import sys
from app.database import SessionLocal
from app.models.service_request import ServiceRequest

db = SessionLocal()

print("Listing all pending ServiceRequests:")
srs = db.query(ServiceRequest).filter(ServiceRequest.status == 'pending').all()
for sr in srs:
    print(f"ID={sr.id} request_type={sr.request_type} emp_id={sr.employee_id} status={sr.status}")

db.close()
