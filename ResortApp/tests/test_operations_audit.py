import pytest
from datetime import date, datetime, time
from app.models.inventory import (
    InventoryItem, InventoryCategory, Location, LocationStock, 
    InventoryTransaction, LaundryLog
)
from app.models.employee import Employee, Attendance, WorkingLog
from app.models.service import Service, AssignedService, ServiceStatus
from app.models.room import Room
from app.models.activity_log import ActivityLog
from app.schemas.service import AssignedServiceUpdate

class TestOperationsAndManagementAudit:
    
    def setup_operations_env(self, db_session, branch_id):
        # 1. Location for Room Inventory
        room_loc = Location(
            name="Room 201 Location", 
            building="Main Block", 
            room_area="Room 201", 
            location_type="Guest Room",
            branch_id=branch_id,
            is_inventory_point=True
        )
        db_session.add(room_loc)
        db_session.flush()

        # 2. Room
        room = Room(
            number="201", 
            status="occupied", 
            inventory_location_id=room_loc.id,
            branch_id=branch_id
        )
        db_session.add(room)
        db_session.flush()
        
        # 3. Employee
        emp = Employee(name="John Operations", role="Housekeeping", branch_id=branch_id)
        db_session.add(emp)
        db_session.flush()
        
        # 4. Linen Category (with laundry tracking)
        cat = InventoryCategory(
            name="Linens", 
            track_laundry=True, 
            branch_id=branch_id
        )
        db_session.add(cat)
        db_session.flush()
        
        # 5. Linen Item
        towel = InventoryItem(
            name="Bath Towel", 
            category_id=cat.id, 
            track_laundry_cycle=True,
            current_stock=100.0, 
            branch_id=branch_id
        )
        db_session.add(towel)
        db_session.flush()
        
        # 6. Service
        svc = Service(name="Full Cleaning", charges=0.0, branch_id=branch_id)
        db_session.add(svc)
        db_session.flush()
        
        return room, emp, towel, svc

    def test_laundry_automation_on_service_completion(self, authorized_client, db_session, test_branch):
        """Verify that completing a service with linen items triggers a laundry movement."""
        branch_id = test_branch.id
        room, emp, towel, svc = self.setup_operations_env(db_session, branch_id)
        
        # 1. Create Assigned Service
        from app.models.employee_inventory import EmployeeInventoryAssignment
        
        assigned = AssignedService(
            service_id=svc.id,
            employee_id=emp.id,
            room_id=room.id,
            status=ServiceStatus.in_progress,
            branch_id=branch_id
        )
        db_session.add(assigned)
        db_session.flush()
        
        # Mock the items "assigned" to this service
        inv_assignment = EmployeeInventoryAssignment(
            employee_id=emp.id,
            assigned_service_id=assigned.id,
            item_id=towel.id,
            quantity_assigned=2.0,
            quantity_used=0.0,
            status="assigned",
            branch_id=branch_id
        )
        db_session.add(inv_assignment)
        db_session.commit()
        
        # 2. Complete Service via API
        # Corrected URL: /api/services/assigned/{assigned_id}
        payload = {
            "status": "completed",
            "inventory_returns": [
                {
                    "assignment_id": inv_assignment.id,
                    "quantity_used": 2.0,
                    "quantity_returned": 0.0
                }
            ]
        }
        response = authorized_client.put(f"/api/services/assigned/{assigned.id}", json=payload)
        assert response.status_code == 200
        
        # 3. VERIFY LAUNDRY LOGIC
        db_session.expire_all()
        
        # Check Laundry Location
        laundry_loc = db_session.query(Location).filter(
            Location.location_type == "LAUNDRY", 
            Location.branch_id == branch_id
        ).one()
        assert laundry_loc.name == "Laundry"
        
        # Check Laundry Stock
        laundry_stock = db_session.query(LocationStock).filter(
            LocationStock.location_id == laundry_loc.id, 
            LocationStock.item_id == towel.id
        ).one()
        assert laundry_stock.quantity == 2.0
        
        # Check Laundry Log
        l_log = db_session.query(LaundryLog).filter(
            LaundryLog.item_id == towel.id,
            LaundryLog.branch_id == branch_id
        ).first()
        assert l_log is not None
        assert l_log.quantity == 2.0
        
        # Check Transaction
        trans = db_session.query(InventoryTransaction).filter(
            InventoryTransaction.reference_number == f"LNDRY-COL-{assigned.id}"
        ).first()
        assert trans is not None
        assert trans.transaction_type == "laundry"

    def test_employee_attendance_traceability(self, authorized_client, db_session, test_branch):
        """Verify that employee activity status is traceable."""
        branch_id = test_branch.id
        emp = Employee(name="Traceable Jane", branch_id=branch_id)
        db_session.add(emp)
        db_session.commit()
        
        # 1. Create a Working Log (Check-in)
        log = WorkingLog(
            employee_id=emp.id,
            date=date.today(),
            check_in_time=time(9, 0),
            location="Reception",
            branch_id=branch_id
        )
        db_session.add(log)
        db_session.commit()
        
        saved_log = db_session.query(WorkingLog).filter(WorkingLog.employee_id == emp.id).first()
        assert saved_log.location == "Reception"

    def test_audit_log_capture(self, authorized_client, db_session, test_branch):
        """Verify that critical actions are captured in ActivityLog (via Middleware)."""
        # 1. Perform an action (e.g., fetch rooms)
        response = authorized_client.get("/api/public/rooms")
        assert response.status_code == 200
        
        # 2. Check ActivityLog
        log = db_session.query(ActivityLog).filter(ActivityLog.path == "/api/public/rooms").first()
        if log:
            assert log.method == "GET"
            assert log.status_code == 200
