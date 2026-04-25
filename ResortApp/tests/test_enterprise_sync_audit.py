import pytest
from datetime import date, timedelta, datetime
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.service import Service
from app.models.branch import Branch
from app.models.user import User, Role
from app.utils.auth import get_password_hash, create_access_token

class TestEnterpriseSyncAudit:

    def setup_branch_data(self, db_session, branch_name, branch_code):
        branch = Branch(name=branch_name, code=branch_code, is_active=True)
        db_session.add(branch)
        db_session.flush()
        
        room = Room(number=f"{branch_code}-101", status="available", branch_id=branch.id)
        db_session.add(room)
        db_session.flush()
        
        booking = Booking(
            guest_name=f"Guest {branch_code}", 
            status="booked", 
            check_in=date.today(), 
            check_out=date.today() + timedelta(days=2),
            branch_id=branch.id
        )
        db_session.add(booking)
        db_session.flush()
        
        br = BookingRoom(booking_id=booking.id, room_id=room.id, branch_id=branch.id)
        db_session.add(br)
        db_session.commit()
        
        return branch, room, booking

    def test_enterprise_kpi_aggregation(self, authorized_client, db_session, test_branch):
        """Verify that super_admin sees aggregated data from all branches."""
        # 1. Setup Data in Branch A (handled by test_branch fixture + ours)
        branch_a = test_branch
        self.setup_branch_data(db_session, "Branch Alpha", "BA") # This creates BA branch
        self.setup_branch_data(db_session, "Branch Beta", "BB")  # This creates BB branch
        
        # 2. Fetch Dashboard KPIs as Super Admin
        # Super admin should see 2 bookings total from BA and BB
        response = authorized_client.get("/api/dashboard/kpis", headers={"X-Branch-ID": "all"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Check booked_rooms (aggregation logic in dashboard.py sums across branches if branch_id is None)
        # BA has 1 room, BB has 1 room. Total 2.
        assert data[0]["booked_rooms"] >= 2

    def test_branch_isolation(self, client, db_session):
        """Verify that branch admins can only see their own branch data."""
        # 1. Create two branches and two users
        from app.models.user import Role
        role = db_session.query(Role).first()
        if not role:
            role = Role(name="admin", permissions="rooms:view")
            db_session.add(role)
            db_session.flush()

        branch_a = Branch(name="Alpha", code="A")
        branch_b = Branch(name="Beta", code="B")
        db_session.add_all([branch_a, branch_b])
        db_session.flush()
        
        user_a = User(
            name="Admin A", email="a@test.com", hashed_password=get_password_hash("pass"),
            branch_id=branch_a.id, role_id=role.id, is_active=True
        )
        user_b = User(
            name="Admin B", email="b@test.com", hashed_password=get_password_hash("pass"),
            branch_id=branch_b.id, role_id=role.id, is_active=True
        )
        db_session.add_all([user_a, user_b])
        db_session.flush()
        
        # 2. Create Room in Branch B only
        room_b = Room(number="B-999", branch_id=branch_b.id)
        db_session.add(room_b)
        db_session.commit()
        
        # 3. Fetch rooms as User A
        token_a = create_access_token({"user_id": user_a.id})
        headers = {"Authorization": f"Bearer {token_a}", "X-Branch-ID": str(branch_a.id)}
        
        response = client.get("/api/rooms", headers=headers)
        assert response.status_code == 200
        rooms = response.json()
        
        # User A should NOT see Room B-999
        for r in rooms:
            assert r["number"] != "B-999"

    def test_web_visibility_sync(self, client, db_session, test_branch):
        """Verify that is_visible_to_guest toggle correctly hides services from public API."""
        branch_id = test_branch.id
        
        # 1. Create Visible Service
        svc_visible = Service(name="Visible Svc", charges=100, is_visible_to_guest=True, branch_id=branch_id)
        db_session.add(svc_visible)
        
        # 2. Create Hidden Service
        svc_hidden = Service(name="Secret Svc", charges=500, is_visible_to_guest=False, branch_id=branch_id)
        db_session.add(svc_hidden)
        db_session.commit()
        
        # 3. Fetch Public Services
        response = client.get(f"/api/public/services?branch_id={branch_id}")
        assert response.status_code == 200
        services = response.json()
        
        # 4. Verify Correct Filtering
        names = [s["name"] for s in services]
        assert "Visible Svc" in names
        assert "Secret Svc" not in names
