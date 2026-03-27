
from app.utils.auth import get_db
from app.curd.service import update_assigned_service_status
from app.schemas.service import AssignedServiceUpdate

db = next(get_db())
assigned_id = 19 # The one that failed

# Run the update again with the same status to trigger the new inventory logic
# Note: My code checks for status change, so I might need to temporarily change it back or bypass the check.
# Let's bypass the check by calling the logic directly or just setting state to in_progress then completed.

from app.models.service import AssignedService, ServiceStatus
assigned = db.query(AssignedService).filter(AssignedService.id == assigned_id).first()
if assigned:
    print(f"Repairing ID {assigned_id}...")
    # Set back to in_progress to trigger transition logic
    assigned.status = ServiceStatus.in_progress
    db.commit()
    
    # Now complete it again
    update_data = AssignedServiceUpdate(status="completed")
    update_assigned_service_status(db, assigned_id, update_data)
    db.commit()
    print("Done.")
