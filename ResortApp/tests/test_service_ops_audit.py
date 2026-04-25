import pytest
from datetime import date, timedelta
from app.models.service import Service, AssignedService, ServiceStatus
from app.models.service_request import ServiceRequest
from app.models.inventory import InventoryItem, Location, StockIssue
from app.models.room import Room, RoomType
from app.models.employee import Employee
from app.models.booking import Booking, BookingRoom
from app.utils.branch_scope import get_branch_id as get_branch_id_scope
from app.utils.auth import get_branch_id as get_branch_id_auth
from main import app

class TestServiceOpsAudit:

    @pytest.fixture(autouse=True)
    def fix_branch_context(self, authorized_client, test_branch, mock_superadmin, db_session):
        app.dependency_overrides.pop(get_branch_id_scope, None)
        app.dependency_overrides.pop(get_branch_id_auth, None)
        
        mock_superadmin.branch_id = test_branch.id
        db_session.add(mock_superadmin)
        db_session.commit()
        
        yield
        
        app.dependency_overrides[get_branch_id_scope] = lambda: None
        app.dependency_overrides[get_branch_id_auth] = lambda: None

    def setup_resort_data(self, db_session, branch_id):
        # Create Room
        rt = RoomType(name="Service Audit Room Type", base_price=100.0, branch_id=branch_id)
        db_session.add(rt)
        db_session.flush()
        room = Room(number="SRV-101", room_type_id=rt.id, branch_id=branch_id)
        db_session.add(room)
        
        # Create Employee
        emp = Employee(name="Audit Cleaner", role="Housekeeping", branch_id=branch_id)
        db_session.add(emp)
        
        # Create Booking
        booking = Booking(
            guest_name="Service Guest",
            guest_mobile="999",
            guest_email="sg@orchid.com",
            check_in=date.today(),
            check_out=date.today() + timedelta(days=1),
            adults=1,
            children=0,
            status="checked-in",
            branch_id=branch_id
        )
        db_session.add(booking)
        db_session.flush()
        br = BookingRoom(booking_id=booking.id, room_id=room.id, branch_id=branch_id)
        db_session.add(br)

        # Create Inventory for Consumption
        loc = Location(name="HK Store", location_type="store", building="Store", floor="1", room_area="100", branch_id=branch_id)
        db_session.add(loc)
        db_session.flush()
        
        # Create Category
        from app.models.inventory import InventoryCategory
        cat = InventoryCategory(name="Service Category", branch_id=branch_id)
        db_session.add(cat)
        db_session.flush()

        item = InventoryItem(
            name="Audit Soap",
            category_id=cat.id,
            current_stock=50.0,
            unit="pcs",
            min_stock_level=5,
            unit_price=10.0,
            branch_id=branch_id
        )
        db_session.add(item)
        db_session.commit()
        return room, emp, booking, item, loc

    def test_master_list_and_consumption_def(self, authorized_client, db_session, test_branch):
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        room, emp, booking, item, loc = self.setup_resort_data(db_session, branch_id)
        service_id = self._create_service(authorized_client, item, headers)
        
        # Verify it shows up in global/branch master list
        response = authorized_client.get("/api/services", headers=headers)
        services = response.json()
        assert any(s["id"] == service_id for s in services)

    def _create_service(self, authorized_client, item, headers):
        service_payload = {
            "name": "Audit Premium Cleaning",
            "charges": 500.0,
            "description": "Deep cleaning",
            "is_visible_to_guest": True,
            "inventory_items": f'[{{"inventory_item_id": {item.id}, "quantity": 2.0}}]'
        }
        response = authorized_client.post("/api/services", data=service_payload, headers=headers)
        if response.status_code != 200:
            print(f"Service setup failed: {response.text}")
        assert response.status_code == 200
        service_data = response.json()
        assert service_data["name"] == "Audit Premium Cleaning"
        
        return service_data["id"]

    def test_assign_work_and_consumption_execution(self, authorized_client, db_session, test_branch):
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        room, emp, booking, item, loc = self.setup_resort_data(db_session, branch_id)
        service_id = self._create_service(authorized_client, item, headers)
        
        # Initial Stock check
        db_session.refresh(item)
        initial_stock = item.current_stock
        assert initial_stock == 50.0
        
        # 1. Assign Work
        assign_payload = {
            "service_id": service_id,
            "employee_id": emp.id,
            "room_id": room.id,
            "booking_id": booking.id
        }
        response = authorized_client.post("/api/services/assign", json=assign_payload, headers=headers)
        assert response.status_code == 200, f"Assignment failed: {response.text}"
        assign_id = response.json()["id"]
        
        # Verify Overview Dashboard detects incomplete work
        # Usually it's in dashboard tasks or service list
        response = authorized_client.get(f"/api/services/assigned?status=pending", headers=headers)
        assigned = response.json()
        assert any(a["id"] == assign_id for a in assigned)
        
        # 2. Consumption: Mark Service as Completed
        complete_payload = {
            "status": "completed"
        }
        response = authorized_client.patch(f"/api/services/assigned/{assign_id}", json=complete_payload, headers=headers)
        assert response.status_code == 200, f"Completion failed: {response.text}"
        
        # Verify Inventory Consumption (2 pieces of soap)
        db_session.refresh(item)
        assert item.current_stock == 48.0, "Service completion did not correctly deduct inventory"

    def test_live_requests_workflow(self, authorized_client, db_session, test_branch):
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        room, emp, booking, item, loc = self.setup_resort_data(db_session, branch_id)
        
        # 1. Create Live Request
        request_payload = {
            "room_id": room.id,
            "request_type": "delivery",
            "description": "Guest needs extra towels"
        }
        response = authorized_client.post("/api/service-requests", json=request_payload, headers=headers)
        assert response.status_code == 200, f"Request failed: {response.text}"
        req_id = response.json()["id"]
        
        # 2. Assign to Employee and Update Status
        update_payload = {
            "employee_id": emp.id,
            "status": "in_progress"
        }
        response = authorized_client.put(f"/api/service-requests/{req_id}", json=update_payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        
        # 3. Mark as Completed
        response = authorized_client.put(f"/api/service-requests/{req_id}", json={"status": "completed"}, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
