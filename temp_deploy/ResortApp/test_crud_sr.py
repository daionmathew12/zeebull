from app.database import SessionLocal
from app.curd.service_request import update_service_request
from app.schemas.service_request import ServiceRequestUpdate
from app.models.service_request import ServiceRequest

db = SessionLocal()
req = db.query(ServiceRequest).first()
if req:
    print("Trying to update req:", req.id, req.request_type)
    try:
        updated = update_service_request(db, req.id, ServiceRequestUpdate(status="completed"))
        print("Success! Status:", updated.status)
    except Exception as e:
        import traceback
        traceback.print_exc()
else:
    print("No service request found")
