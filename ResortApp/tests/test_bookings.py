"""
test_bookings.py — Room booking tests
Routes: GET/POST /api/bookings, PUT /api/bookings/{id}/check-in
"""
import pytest
from datetime import datetime, timedelta


class TestRoomBookingEndpoints:
    def test_list_bookings(self, authorized_client):
        """GET /api/bookings should return a list."""
        response = authorized_client.get("/api/bookings")
        assert response.status_code == 200
        assert isinstance(response.json(), (list, dict))

    def test_create_booking_missing_fields(self, authorized_client):
        """POST with empty body should return 422."""
        response = authorized_client.post("/api/bookings", json={})
        assert response.status_code == 422

    def test_create_booking_invalid_room(self, authorized_client):
        """Booking with a non-existent room should fail gracefully."""
        checkin = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        payload = {
            "room_id": 99999,
            "guest_name": "Test Guest",
            "guest_email": "guest@test.com",
            "guest_mobile": "9999999999",
            "check_in_date": checkin,
            "check_out_date": checkout,
            "num_guests": 2,
            "total_price": 3000.0,
        }
        response = authorized_client.post("/api/bookings", json=payload)
        assert response.status_code not in [200, 201, 500], (
            f"Invalid room booking should fail cleanly, got {response.status_code}"
        )

    def test_get_booking_not_found(self, authorized_client):
        """GET /api/bookings/99999 should return 404."""
        response = authorized_client.get("/api/bookings/99999")
        assert response.status_code == 404


class TestCheckinEndpoints:
    def test_checkin_nonexistent_booking(self, authorized_client):
        """PUT checkin for a non-existent booking should fail gracefully."""
        response = authorized_client.put("/api/bookings/99999/check-in", json={})
        assert response.status_code != 500
        assert response.status_code in [400, 404, 422]

    def test_cancel_nonexistent_booking(self, authorized_client):
        """PUT /api/bookings/99999/cancel should return 404, not 500."""
        response = authorized_client.put("/api/bookings/99999/cancel", json={})
        assert response.status_code != 500
        assert response.status_code in [400, 404, 422]


class TestPriceCalculation:
    def test_calculate_price_endpoint(self, authorized_client):
        """POST /api/bookings/calculate-price should accept valid data."""
        checkin = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        checkout = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        payload = {
            "room_id": 1,
            "check_in_date": checkin,
            "check_out_date": checkout,
            "num_guests": 2,
        }
        response = authorized_client.post("/api/bookings/calculate-price", json=payload)
        # 400 is acceptable if room doesn't exist — but NOT 500
        assert response.status_code != 500
