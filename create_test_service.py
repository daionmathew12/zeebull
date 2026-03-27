
from app.utils.auth import get_db
from app.models.service import Service, AssignedService
from app.models.room import Room
from app.models.employee import Employee
from app.models.employee_inventory import EmployeeInventoryAssignment
from datetime import datetime

db = next(get_db())

service = db.query(Service).filter(Service.id == 3).first()
if not service:
    service = db.query(Service).first()
room = db.query(Room).filter(Room.id == 2).first() # Room 101, Branch 2
employee = db.query(Employee).first()

if service and room and employee:
    print(f"Assigning Service '{service.name}' to Room '{room.number}' and Employee '{employee.id}'")
    assigned = AssignedService(
        service_id=service.id,
        employee_id=employee.id,
        room_id=room.id,
        status="in_progress",
        assigned_at=datetime.utcnow(),
        branch_id=room.branch_id
    )
    db.add(assigned)
    db.commit()
    db.refresh(assigned)
    print(f"Created AssignedService ID: {assigned.id}")

    # Assignment for Bedsheet (ID 6)
    db.add(EmployeeInventoryAssignment(
        employee_id=employee.id,
        item_id=6,
        quantity_assigned=1.0,
        status="assigned",
        assigned_service_id=assigned.id,
        assigned_at=datetime.utcnow(),
        branch_id=room.branch_id
    ))
    
    # Assignment for Oil (ID 2)
    db.add(EmployeeInventoryAssignment(
        employee_id=employee.id,
        item_id=2,
        quantity_assigned=0.5,
        status="assigned",
        assigned_service_id=assigned.id,
        assigned_at=datetime.utcnow(),
        branch_id=room.branch_id
    ))
    
    db.commit()
    print(f"Created Assignments for Svc {assigned.id}")
else:
    print("Missing data to create test service.")
