from app.database import SessionLocal
from app.models.service import AssignedService, Service
from datetime import datetime, timezone

db = SessionLocal()
svc = db.query(Service).first()
if not svc:
    svc = Service(name="Test Service", price=100)
    db.add(svc)
    db.commit()
    db.refresh(svc)

a = AssignedService(
    service_id=svc.id,
    room_id=6,
    status="pending",
    assigned_at=datetime.now(timezone.utc),
    branch_id=1
)
db.add(a)
db.commit()
print(f"Assigned Service created for Room 101 with ID {a.id}")
