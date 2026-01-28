from app.database import SessionLocal
from app.models.service import AssignedService
from app.models.employee_inventory import EmployeeInventoryAssignment
from app.models.inventory import InventoryTransaction
from sqlalchemy import desc

db = SessionLocal()

print("--- Checking Latest Assigned Service ---")
last_assigned = db.query(AssignedService).order_by(desc(AssignedService.id)).first()

if last_assigned:
    print(f"Latest Assigned Service ID: {last_assigned.id}")
    print(f"Service ID: {last_assigned.service_id}")
    
    print("\n--- Checking Employee Inventory Assignments ---")
    assignments = db.query(EmployeeInventoryAssignment).filter(
        EmployeeInventoryAssignment.assigned_service_id == last_assigned.id
    ).all()
    
    if assignments:
        print(f"Found {len(assignments)} assignments:")
        for a in assignments:
            print(f" - Item ID: {a.item_id}, Assigned: {a.quantity_assigned}, Used: {a.quantity_used}")
    else:
        print("NO EmployeeInventoryAssignment records found!")

    print("\n--- Checking Transactions ---")
    txns = db.query(InventoryTransaction).filter(
        InventoryTransaction.reference_number == f"SVC-ASSIGN-{last_assigned.id}"
    ).all()
    if txns:
        for t in txns:
            print(f" - Txn: {t.transaction_type}, Item: {t.item_id}, Qty: {t.quantity}")
    else:
        print("NO Transactions found!")

else:
    print("No Assigned Services found.")

print("\n--- Model Path Check ---")
import os
if os.path.exists("c:/releasing/New Orchid/ResortApp/app/models/employee_inventory.py"):
    print("app/models/employee_inventory.py exists.")
else:
    print("app/models/employee_inventory.py DOES NOT exist.")

print("\n--- Raw Table Check ---")
from sqlalchemy import text
try:
    count = db.execute(text("SELECT count(*) FROM assigned_services")).scalar()
    print(f"assigned_services table count: {count}")
except Exception as e:
    print(f"Error checking assigned_services: {e}")

try:
    count = db.execute(text("SELECT count(*) FROM employee_inventory_assignments")).scalar()
    print(f"employee_inventory_assignments table count: {count}")
except Exception as e:
    print(f"Error checking employee_inventory_assignments: {e}")
