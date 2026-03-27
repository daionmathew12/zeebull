
from app.utils.auth import get_db
from app.models.service import AssignedService, service_inventory_item
from app.models.inventory import InventoryItem
from sqlalchemy import select

db = next(get_db())

# Find an assigned service that is 'in_progress' and has items
assigned = db.query(AssignedService).filter(AssignedService.status == "in_progress").first()

if assigned:
    print(f"Found active service ID: {assigned.id}, Status: {assigned.status}, Branch: {assigned.branch_id}")
    # Check items
    items = db.query(InventoryItem).join(
        service_inventory_item, service_inventory_item.c.inventory_item_id == InventoryItem.id
    ).filter(service_inventory_item.c.service_id == assigned.service_id).all()
    
    print(f"Items linked to service definition:")
    for item in items:
        print(f"  - {item.name} (ID: {item.id}), Track Laundry: {item.track_laundry_cycle}")
else:
    print("No active service found.")
