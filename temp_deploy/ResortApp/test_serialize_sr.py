from app.database import SessionLocal
from app.models.service_request import ServiceRequest
from app.schemas.service_request import ServiceRequestOut

db = SessionLocal()
req = db.query(ServiceRequest).first()
if req:
    try:
        # FastAPI basically does this:
        out = ServiceRequestOut.from_orm(req)
        # Or in v2: out = ServiceRequestOut.model_validate(req)
        print("Success! Serialized:", out.dict())
    except Exception as e:
        import traceback
        traceback.print_exc()
else:
    print("No service request found")
