import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app directory to path
sys.path.append(os.getcwd())

from app.database import get_db, Base
from app.models.service import AssignedService, Service
from app.models.employee_inventory import EmployeeInventoryAssignment

def check_latest_service():
    db = next(get_db())
    try:
        # Get latest assigned service
        latest_service = db.query(AssignedService).order_by(AssignedService.assigned_at.desc()).first()
        
        if not latest_service:
            print("No assigned services found.")
            return

        print(f"Latest Assigned Service ID: {latest_service.id}")
        print(f"Service Name: {latest_service.service.name}")
        print(f"Status: {latest_service.status}")
        
        # Check assignments
        assignments = db.query(EmployeeInventoryAssignment).filter(
            EmployeeInventoryAssignment.assigned_service_id == latest_service.id
        ).all()
        
        print(f"Found {len(assignments)} EmployeeInventoryAssignments:")
        for a in assignments:
            print(f" - Assignment ID: {a.id}, Item ID: {a.item_id}, Qty: {a.quantity_assigned}")
            
        # Check if service has default items
        service_def = latest_service.service
        print(f"Service Definition ID: {service_def.id} has {len(service_def.inventory_items)} default inventory items")
        for i in service_def.inventory_items:
             print(f" - Item ID: {i.inventory_item_id}, Qty: {i.quantity}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_latest_service()
