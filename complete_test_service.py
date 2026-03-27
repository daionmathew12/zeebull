
from app.utils.auth import get_db
from app.curd.service import update_assigned_service_status
from app.schemas.service import AssignedServiceUpdate, InventoryReturnItem

db = next(get_db())
assigned_id = 16

update_data = AssignedServiceUpdate(
    status="completed",
    inventory_returns=[
        InventoryReturnItem(inventory_item_id=6, quantity_returned=0.0, quantity_used=1.0),
        InventoryReturnItem(inventory_item_id=2, quantity_returned=0.0, quantity_used=0.5)
    ]
)

try:
    print(f"Completing Assigned Service {assigned_id}...")
    result = update_assigned_service_status(
        db, 
        assigned_id=assigned_id, 
        update_data=update_data, 
        updated_by=1
    )
    print("Completion successful!")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Completion failed: {e}")
