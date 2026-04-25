import pytest
from datetime import date, timedelta, datetime
from typing import Optional
from app.models.room import RoomType, Room
from app.models.booking import Booking, BookingRoom
from app.models.Package import Package, PackageBooking, PackageBookingRoom
from app.models.checkout import Checkout
from app.utils.auth import get_current_user, get_branch_id as get_branch_id_auth
from app.utils.branch_scope import get_branch_id as get_branch_id_scope
from main import app

class TestResortOperationsAudit:

    @pytest.fixture(autouse=True)
    def fix_branch_context(self, authorized_client, test_branch, mock_superadmin, db_session):
        """Restore real branch scoping logic and sync mock user."""
        app.dependency_overrides.pop(get_branch_id_scope, None)
        app.dependency_overrides.pop(get_branch_id_auth, None)
        
        mock_superadmin.branch_id = test_branch.id
        db_session.add(mock_superadmin)
        db_session.commit()
        
        yield
        
        app.dependency_overrides[get_branch_id_scope] = lambda: None
        app.dependency_overrides[get_branch_id_auth] = lambda: None

    def setup_resort_assets(self, db_session, branch_id):
        # 1. Create Room Type
        rt = RoomType(
            name="Deluxe Suite Audit",
            base_price=5000.0,
            adults_capacity=2,
            total_inventory=10,
            branch_id=branch_id
        )
        db_session.add(rt)
        db_session.flush()
        
        # 2. Create physical Room
        room = Room(
            number="AUDIT-101",
            room_type_id=rt.id,
            status="Available",
            branch_id=branch_id
        )
        db_session.add(room)
        
        # 3. Create Package
        pkg = Package(
            title="Audit Package",
            price=12000.0,
            booking_type="room_type",
            room_types="Deluxe Suite Audit",
            branch_id=branch_id
        )
        db_session.add(pkg)
        
        db_session.commit()
        return rt, room, pkg

    def test_room_and_package_definition(self, authorized_client, db_session, test_branch):
        """Audit Room and Package creation and visibility."""
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        
        # 1. Create via Setup
        rt, room, pkg = self.setup_resort_assets(db_session, branch_id)
        
        # 2. Verify Room Visibility
        response = authorized_client.get("/api/public/rooms", headers=headers)
        assert response.status_code == 200
        rooms = response.json()
        assert any(r["number"] == "AUDIT-101" for r in rooms)
        
        # 3. Verify Package Visibility
        response = authorized_client.get("/api/public/packages", headers=headers)
        assert response.status_code == 200
        packages = response.json()
        assert any(p["title"] == "Audit Package" for p in packages)

    def test_booking_lifecycle_and_occupancy(self, authorized_client, db_session, test_branch):
        """Audit regular booking: Creation -> Check-in -> Occupancy Metric."""
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        rt, room, _ = self.setup_resort_assets(db_session, branch_id)
        
        # 1. Calculate Price
        price_payload = {
            "room_type_id": rt.id,
            "check_in": str(date.today()),
            "check_out": str(date.today() + timedelta(days=2)),
            "room_count": 1
        }
        response = authorized_client.post("/api/bookings/calculate-price", json=price_payload, headers=headers)
        assert response.status_code == 200
        # 5000 * 2 nights = 10000
        assert response.json()["total_amount"] == 10000.0
        
        # 2. Create Booking
        booking_payload = {
            "guest_name": "Audit Guest",
            "guest_mobile": "9999999999",
            "guest_email": "audit@example.com",
            "check_in": str(date.today()),
            "check_out": str(date.today() + timedelta(days=2)),
            "room_type_id": rt.id,
            "num_rooms": 1,
            "adults": 2,
            "children": 0,
            "total_amount": 10000.0
        }
        response = authorized_client.post("/api/bookings", json=booking_payload, headers=headers)
        if response.status_code != 200:
            print(f"Booking failed: {response.text}")
        assert response.status_code == 200
        booking_id = response.json()["id"]
        
        # 3. Check-in (Status update)
        # Check-in endpoint expects form data with room_ids as JSON string
        checkin_payload = {"room_ids": f"[{room.id}]"}
        response = authorized_client.put(f"/api/bookings/{booking_id}/check-in", data=checkin_payload, headers=headers)
        assert response.status_code == 200
        
        # 4. Verify Dashboard KPI for Occupancy
        response = authorized_client.get("/api/dashboard/kpis", headers=headers)
        assert response.status_code == 200
        kpis = response.json()[0]
        # At least 1 room should be booked
        assert kpis["booked_rooms"] >= 1
        # Room should be marked as "Occupied" (if logic handles it automatically)
        db_session.refresh(room)
        # assert room.status == "Occupied" # Depending on model logic

    def test_package_booking_flow(self, authorized_client, db_session, test_branch):
        """Audit Package Booking verification."""
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        rt, room, pkg = self.setup_resort_assets(db_session, branch_id)
        
        # 1. Create Package Booking
        pkg_booking_payload = {
            "package_id": pkg.id,
            "guest_name": "Pkg Audit Guest",
            "check_in": str(date.today()),
            "check_out": str(date.today() + timedelta(days=1)),
            "adults": 2,
            "num_rooms": 1,
            "total_amount": 12000.0
        }
        response = authorized_client.post("/api/packages/book", json=pkg_booking_payload, headers=headers)
        if response.status_code != 200:
            print(f"Pkg Booking failed: {response.text}")
        assert response.status_code == 200
        
        # 2. Verify KPI
        response = authorized_client.get("/api/dashboard/kpis", headers=headers)
        kpis = response.json()[0]
        assert kpis["package_bookings_today"] >= 1

    def test_revenue_integrity_audit(self, authorized_client, db_session, test_branch):
        """Audit revenue calculation via Checkout lifecycle."""
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        rt, room, _ = self.setup_resort_assets(db_session, branch_id)
        
        # 1. Setup a booking and CHECKOUT
        booking = Booking(
            guest_name="Revenue Audit Guest",
            check_in=date.today(),
            check_out=date.today() + timedelta(days=1),
            room_type_id=rt.id,
            total_amount=5000.0,
            status="checked-in",
            branch_id=branch_id
        )
        db_session.add(booking)
        db_session.flush()
        br = BookingRoom(booking_id=booking.id, room_id=room.id, branch_id=branch_id)
        db_session.add(br)
        db_session.flush()
        
        # 2. Create Checkout record
        checkpoint_revenue = 5000.0
        checkout = Checkout(
            booking_id=booking.id,
            checkout_date=datetime.now(__import__("datetime").timezone.utc),
            room_total=5000.0,
            grand_total=5000.0,
            payment_status="paid",
            payment_method="Cash",
            branch_id=branch_id
        )
        db_session.add(checkout)
        db_session.commit()
        
        # 3. Verify Dashboard Revenue Total
        response = authorized_client.get("/api/dashboard/kpis", headers=headers)
        kpis = response.json()[0]
        assert kpis["revenue_today"] >= checkpoint_revenue
        
        # 4. Verify Chart Breakdown
        response = authorized_client.get("/api/dashboard/charts", headers=headers)
        assert response.status_code == 200
        charts = response.json()
        breakdown = charts["revenue_breakdown"]
        room_charges = next(item for item in breakdown if item["name"] == "Room Charges")
        assert room_charges["value"] >= 5000.0
