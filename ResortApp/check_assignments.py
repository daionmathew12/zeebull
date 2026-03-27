
from app.utils.auth import get_db
from app.models.employee_inventory import EmployeeInventoryAssignment
from sqlalchemy import text

db = next(get_db())

# List all assignments to see if extra items are there
assignments = db.query(EmployeeInventoryAssignment).all()
print(f"Total assignments: {len(assignments)}")
for a in assignments:
    print(f"ID={a.id}, SvcID={a.assigned_service_id}, Item={a.item.name}, Qty={a.quantity_assigned}")
