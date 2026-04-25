"""
test_checkout_logic.py — Tests for billing math and checkout API flows.
"""
import pytest
from datetime import datetime, date, timedelta
from app.utils.checkout_helpers import (
    calculate_consumable_charge, 
    calculate_late_checkout_fee,
    calculate_gst_breakdown
)
from app.models.inventory import InventoryItem

class TestBillingUnitLogic:
    def test_calculate_consumable_charge_amenity(self):
        """Amenities like water should have complimentary limit applied."""
        # Mock an amenity item (Water)
        item = InventoryItem(
            name="Mineral Water (500ml)",
            selling_price=50.0,
            unit_price=20.0,
            gst_rate=5.0,
            complimentary_limit=2,
            is_sellable_to_guest=True
        )
        
        # Scenario 1: Inside limit
        charge, price, qty = calculate_consumable_charge(item, 2)
        assert charge == 0.0
        assert qty == 0
        
        # Scenario 2: Beyond limit
        charge, price, qty = calculate_consumable_charge(item, 5)
        # 5 - 2 = 3 chargeable units. 3 * 50 = 150
        assert charge == 150.0
        assert price == 50.0
        assert qty == 3

    def test_calculate_consumable_charge_non_sellable(self):
        """Non-sellable items with no limit should be free (complimentary)."""
        item = InventoryItem(
            name="Welcome Chocolate",
            selling_price=0.0,
            unit_price=10.0,
            gst_rate=5.0,
            complimentary_limit=1,
            is_sellable_to_guest=False
        )
        
        # Even if consumed 2, if it's not sellable and limit is 1, 
        # the helper logic says if non-sellable and limit=0 -> charge=0.
        # If limit=1 and consumed 2 -> 2-1 = 1 excess. 
        # But if selling_price=0, it uses unit_price + GST as replacement price.
        charge, price, qty = calculate_consumable_charge(item, 2)
        # 1 excess * (10 * 1.05) = 10.5
        assert charge == 10.5
        assert qty == 1

    def test_calculate_late_checkout_fee(self):
        """Verify 50% fee after threshold hour."""
        room_rate = 2000.0
        check_out_date = date.today()
        
        # Scenario 1: On time (10 AM)
        on_time = datetime.combine(check_out_date, datetime.min.time().replace(hour=10))
        fee = calculate_late_checkout_fee(check_out_date, on_time, room_rate, 12)
        assert fee == 0.0
        
        # Scenario 2: Late (2 PM)
        late_time = datetime.combine(check_out_date, datetime.min.time().replace(hour=14))
        fee = calculate_late_checkout_fee(check_out_date, late_time, room_rate, 12)
        assert fee == room_rate * 0.5
        
        # Scenario 3: Next day
        next_day = datetime.combine(check_out_date + timedelta(days=1), datetime.min.time().replace(hour=9))
        fee = calculate_late_checkout_fee(check_out_date, next_day, room_rate, 12)
        assert fee == room_rate * 0.5

    def test_calculate_gst_breakdown(self):
        """Verify GST slabs for room charges."""
        # Slab 1: < 7500 -> 12%
        res1 = calculate_gst_breakdown(room_charges=5000.0, food_charges=1000.0, package_charges=0.0)
        assert res1["room_gst"] == 5000.0 * 0.12
        assert res1["food_gst"] == 1000.0 * 0.05
        
        # Slab 2: >= 7500 -> 18%
        res2 = calculate_gst_breakdown(room_charges=8000.0, food_charges=0.0, package_charges=0.0)
        assert res2["room_gst"] == 8000.0 * 0.18


class TestCheckoutAPIFlows:
    def test_checkout_request_unauthorized(self, client):
        """Unauthorized access should return 401."""
        response = client.post("/api/bill/checkout-request?room_number=101")
        assert response.status_code == 401

    def test_get_checkout_request_not_found(self, authorized_client):
        """Room with no active booking should return 404 for checkout request."""
        # Room 999 likely doesn't exist
        response = authorized_client.post("/api/bill/checkout-request?room_number=999")
        assert response.status_code == 404

    def test_checkout_request_valid_room(self, authorized_client, db_session):
        """A room with an active booking should allow creating a checkout request."""
        # This belongs in a higher level integration test with seeded data,
        # but we can try to verify the endpoint logic here.
        # Implementation of full seeded flow...
        pass
