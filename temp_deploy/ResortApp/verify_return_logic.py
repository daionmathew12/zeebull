
import sys
import os
import random
import string
from datetime import datetime

# Setup environment
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.service import Service, AssignedService, service_inventory_item
from app.models.inventory import InventoryItem, InventoryTransaction, Location, LocationStock
from app.models.employee_inventory import EmployeeInventoryAssignment
from app.models.employee import Employee
from app.models.room import Room
from app.schemas.service import AssignedServiceUpdate, InventoryReturnItem

# Database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./resort.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def run_test():
    print("Starting Return Logic Verification...")
    
    # 1. Create a test Inventory Item
    item_name = f"TestItem_{''.join(random.choices(string.ascii_letters, k=5))}"
    item = InventoryItem(
        name=item_name,
        unit="pcs",
        current_stock=100.0,
        unit_price=10.0,
        min_stock_level=10.0
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    print(f"Created Inventory Item: {item.name} (ID: {item.id}), Stock: {item.current_stock}")

    # 2. Create a test Service that uses this item
    service = Service(
        name=f"TestService_{''.join(random.choices(string.ascii_letters, k=5))}",
        charges=100.0,
        is_visible_to_guest=True
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    print(f"Created Service: {service.name} (ID: {service.id})")

    # Link inventory
    db.execute(service_inventory_item.insert().values(
        service_id=service.id,
        inventory_item_id=item.id,
        quantity=5.0
    ))
    db.commit()
    print(f"Linked 5.0 {item.name} to Service")

    # 3. Assign Service
    # Need Employee and Room
    employee = db.query(Employee).first()
    room = db.query(Room).first()
    
    if not employee or not room:
        print("Error: Need at least one employee and one room in DB")
        return

    from app.curd.service import create_assigned_service
    from app.schemas.service import AssignedServiceCreate
    
    assign_payload = AssignedServiceCreate(
        service_id=service.id,
        employee_id=employee.id,
        room_id=room.id
    )
    
    # This calls the CRUD function which should create EmployeeInventoryAssignment
    assigned_svc = create_assigned_service(db, assign_payload)
    db.commit()
    print(f"Assigned Service ID: {assigned_svc.id}")
    
    # Verify EmployeeInventoryAssignment
    emp_inv = db.query(EmployeeInventoryAssignment).filter(
        EmployeeInventoryAssignment.assigned_service_id == assigned_svc.id,
        EmployeeInventoryAssignment.item_id == item.id
    ).first()
    
    if emp_inv:
        print(f"Verified EmployeeInventoryAssignment created: ID {emp_inv.id}, Assigned: {emp_inv.quantity_assigned}")
    else:
        print("ERROR: EmployeeInventoryAssignment NOT created!")

    # 4. Update Status to Completed with Returns
    from app.curd.service import update_assigned_service_status
    
    # Return 2.0 items
    return_payload = AssignedServiceUpdate(
        status="completed",
        inventory_returns=[
            InventoryReturnItem(
                assignment_id=emp_inv.id if emp_inv else None, # Use Assignment ID if it exists
                inventory_item_id=item.id, # Fallback
                quantity_returned=2.0,
                quantity_used=3.0,
                notes="Test Return"
            )
        ]
    )
    
    print("\nCompleting service with 2.0 returns...")
    update_assigned_service_status(db, assigned_svc.id, return_payload)
    
    # 5. Verify Stock and Transaction
    db.refresh(item)
    print(f"\nFinal Item Stock: {item.current_stock}")
    
    # Expected: 100 - 5 (assigned) + 2 (returned) = 97
    # Note: assign deducts 5. Return adds 2.
    # Initial: 100.
    # After assign: 95.
    # After return: 97.
    
    if item.current_stock == 97.0:
        print("SUCCESS: Stock updated correctly.")
    else:
        print(f"FAILURE: Stock incorrect. Expected 97.0, Got {item.current_stock}")
        
    # Verify Transaction
    txn = db.query(InventoryTransaction).filter(
        InventoryTransaction.reference_number == f"SVC-RETURN-{assigned_svc.id}"
    ).first()
    
    if txn:
        print(f"SUCCESS: Transaction found: {txn.transaction_type} {txn.quantity} for {txn.reference_number}")
    else:
        print("FAILURE: Return Transaction NOT found.")

    # 6. Test Fallback (No Assignment Record)
    # Create another mock completion with an item ID but NO assignment ID/record match
    print("\nTesting Fallback (simulating missing assignment record)...")
    
    # We'll try to return an item that WASN'T in the assignment, forcing the lookup to fail
    # In current code, this should Skip/Fail. We want to see it fail to confirm behavior.
    
    # ... actually let's just see if the first part passes.

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        import traceback
        traceback.print_exc()
