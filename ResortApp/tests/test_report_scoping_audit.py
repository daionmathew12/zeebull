import pytest
from datetime import date, timedelta, datetime
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.expense import Expense
from app.models.branch import Branch
from app.models.user import User, Role
from app.models.employee import Employee
from app.models.service import Service, AssignedService
from app.models.checkout import Checkout
from app.utils.auth import get_password_hash, create_access_token

class TestReportScopingAudit:
    """
    Comprehensive audit tests for reporting multi-tenancy.
    Verifies that:
    1. Branch A data is isolated from Branch B requests.
    2. Enterprise view (X-Branch-ID: all) aggregates data accurately.
    3. Specific branch views for Superadmins return only that branch's data.
    """

    def seed_branch_data(self, db_session, name, code):
        """Seeds a branch with a full set of reportable data."""
        # 1. Create Branch
        branch = Branch(name=name, code=code, is_active=True)
        db_session.add(branch)
        db_session.flush()

        # 2. Create Employee/User
        role = db_session.query(Role).filter(Role.name == "admin").first()
        if not role:
            role = Role(name="admin", permissions="all")
            db_session.add(role)
            db_session.flush()

        user = User(
            name=f"Admin {code}", 
            email=f"admin@{code}.com", 
            hashed_password=get_password_hash("password"),
            branch_id=branch.id,
            role_id=role.id,
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        employee = Employee(
            name=f"Emp {code}",
            user_id=user.id,
            branch_id=branch.id,
            role="Manager",
            join_date=date.today()
        )
        db_session.add(employee)
        db_session.flush()

        # 3. Create Room
        room = Room(number=f"{code}-101", status="available", branch_id=branch.id)
        db_session.add(room)
        db_session.flush()

        # 4. Create Booking
        booking = Booking(
            guest_name=f"Guest {code}", 
            guest_mobile=f"12345{code}",
            guest_email=f"guest@{code}.com",
            status="checked-in", 
            check_in=date.today(), 
            check_out=date.today() + timedelta(days=2),
            branch_id=branch.id,
            user_id=user.id
        )
        db_session.add(booking)
        db_session.flush()
        
        br = BookingRoom(booking_id=booking.id, room_id=room.id, branch_id=branch.id)
        db_session.add(br)

        # 5. Create Food Order
        order = FoodOrder(
            room_id=room.id,
            branch_id=branch.id,
            assigned_employee_id=employee.id,
            amount=500.0,
            status="delivered"
        )
        db_session.add(order)

        # 6. Create Expense
        expense = Expense(
            description=f"Maintenance {code}",
            amount=1000.0,
            category="Repair",
            branch_id=branch.id,
            employee_id=employee.id,
            date=date.today()
        )
        db_session.add(expense)

        # 7. Create Service Charge via Checkout (historical)
        checkout = Checkout(
            booking_id=booking.id,
            room_number=room.number,
            branch_id=branch.id,
            room_total=2000.0,
            food_total=500.0,
            service_total=300.0,
            grand_total=2800.0,
            checkout_date=date.today()
        )
        db_session.add(checkout)

        db_session.commit()
        return branch, user, employee, booking, room

    def test_report_isolation(self, authorized_client, db_session):
        """Test that data is isolated between branches for standard report requests."""
        # Seed Branch A and Branch B
        branch_a, user_a, emp_a, book_a, room_a = self.seed_branch_data(db_session, "Alpha", "A")
        branch_b, user_b, emp_b, book_b, room_b = self.seed_branch_data(db_session, "Beta", "B")

        # 1. Test Room Bookings - Requesting Branch A
        headers_a = {"X-Branch-ID": str(branch_a.id)}
        resp = authorized_client.get("/api/reports/room-bookings", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["guest_name"] == "Guest A"

        # 2. Test Food Orders - Requesting Branch B
        headers_b = {"X-Branch-ID": str(branch_b.id)}
        resp = authorized_client.get("/api/reports/food-orders", headers=headers_b)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["amount"] == 500.0
        # Verification of guest mapping in food order report
        assert data[0]["guest_name"] == "Guest B"

        # 3. Test Expenses - Requesting Branch A
        resp = authorized_client.get("/api/reports/expenses", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["description"] == "Maintenance A"

    def test_enterprise_aggregated_reports(self, authorized_client, db_session):
        """Test that X-Branch-ID: all correctly aggregates data across branches."""
        # Seed Branch X and Branch Y
        branch_x, _, _, _, _ = self.seed_branch_data(db_session, "X-Ray", "X")
        branch_y, _, _, _, _ = self.seed_branch_data(db_session, "Yankee", "Y")

        headers_all = {"X-Branch-ID": "all"}

        # 1. Test Aggregated Bookings
        resp = authorized_client.get("/api/reports/room-bookings", headers=headers_all)
        assert resp.status_code == 200
        data = resp.json()
        # Should find at least 2 bookings (one from X, one from Y)
        assert len(data) >= 2
        guests = [b["guest_name"] for b in data]
        assert "Guest X" in guests
        assert "Guest Y" in guests

        # 2. Test Aggregated Expenses
        resp = authorized_client.get("/api/reports/expenses", headers=headers_all)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        descriptions = [e["description"] for e in data]
        assert "Maintenance X" in descriptions
        assert "Maintenance Y" in descriptions

    def test_guest_profile_isolation(self, authorized_client, db_session):
        """Test that Guest Profile report respects branch scoping."""
        branch_a, _, _, book_a, _ = self.seed_branch_data(db_session, "Alpha", "A")
        branch_b, _, _, book_b, _ = self.seed_branch_data(db_session, "Beta", "B")

        # Search for Guest A in Branch A - Should succeed
        headers_a = {"X-Branch-ID": str(branch_a.id)}
        resp = authorized_client.get(f"/api/reports/guest-profile?guest_mobile={book_a.guest_mobile}", headers=headers_a)
        assert resp.status_code == 200
        assert resp.json()["guest_details"]["name"] == "Guest A"

        # Search for Guest A in Branch B - Should fail (isolated)
        headers_b = {"X-Branch-ID": str(branch_b.id)}
        resp = authorized_client.get(f"/api/reports/guest-profile?guest_mobile={book_a.guest_mobile}", headers=headers_b)
        assert resp.status_code == 404

        # Search for Guest A with Enterprise view - Should succeed
        headers_all = {"X-Branch-ID": "all"}
        resp = authorized_client.get(f"/api/reports/guest-profile?guest_mobile={book_a.guest_mobile}", headers=headers_all)
        assert resp.status_code == 200
        assert resp.json()["guest_details"]["name"] == "Guest A"

    def test_employee_checkin_summary_scoping(self, authorized_client, db_session):
        """Test that check-in by employee report respects branch scoping."""
        branch_a, _, emp_a, _, _ = self.seed_branch_data(db_session, "Alpha", "A")
        branch_b, _, emp_b, _, _ = self.seed_branch_data(db_session, "Beta", "B")

        # Branch A report
        headers_a = {"X-Branch-ID": str(branch_a.id)}
        resp = authorized_client.get("/api/reports/checkin-by-employee", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()
        names = [r["employee_name"] for r in data]
        assert f"Admin A" in names
        assert f"Admin B" not in names

        # Enterprise report
        headers_all = {"X-Branch-ID": "all"}
        resp = authorized_client.get("/api/reports/checkin-by-employee", headers=headers_all)
        assert resp.status_code == 200
        data = resp.json()
        names = [r["employee_name"] for r in data]
        assert f"Admin A" in names
        assert f"Admin B" in names
