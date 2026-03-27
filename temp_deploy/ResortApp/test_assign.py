from app.database import SessionLocal
from app.models.service import AssignedService

db = SessionLocal()
req = db.query(AssignedService).first()
if req:
    print(f"Trying to update assigned req: {req.id}")
    try:
        req.status = "completed"
        db.commit()
        db.refresh(req)
        from app.schemas.service import AssignedServiceOut
        
        # Manually load inventory items in _serialize_assigned_service to avoid DetachedInstanceError or similar?
        # Let's just try serializing it using the Pydantic model exactly like the endpoint does
        out = AssignedServiceOut.from_orm(req)
        print("Success! Status:", out.status)
        print("Serialized Dict:", out.dict())
    except Exception as e:
        import traceback
        traceback.print_exc()
else:
    print("No assigned service request found")
