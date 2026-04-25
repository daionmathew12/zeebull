"""
test_billing_calculations.py — End-to-end billing and calculation verification.
"""
import pytest
from datetime import datetime, date, timedelta
from app.models.room import Room, RoomType
from app.models.booking import Booking, BookingRoom
from app.models.inventory import InventoryItem, LocationStock, InventoryCategory, Location
from app.models.checkout import CheckoutRequest as CheckoutRequestModel

def seed_full_booking_data(db, branch, room_price):
    """Seed data for a complete checkout flow."""
    branch_id = branch.id
    
    # 1. Create Room Type & Room
    rtype = RoomType(name="Standard Test", base_price=room_price, branch_id=branch_id)
    db.add(rtype)
    db.flush()
    
    room = Room(number="202", branch_id=branch_id, room_type_id=rtype.id)
    db.add(room)
    db.flush()
    
    # 2. Create Guest & Booking
    booking = Booking(
        guest_name="Test Billing Guest",
        check_in=date.today() - timedelta(days=2),
        check_out=date.today(),
        status="checked-in",
        branch_id=branch_id,
        display_id="BK-202",
        total_amount=room_price * 2
    )
    db.add(booking)
    db.flush()
    
    br = BookingRoom(booking_id=booking.id, room_id=room.id, branch_id=branch_id)
    db.add(br)
    db.flush()
    
    # 3. Create Inventory Category & Item (for consumable charges)
    category = InventoryCategory(name="Minibar", branch_id=branch_id)
    db.add(category)
    db.flush()
    
    snack = InventoryItem(
        name="Potato Chips",
        category_id=category.id,
        selling_price=100.0,
        is_sellable_to_guest=True,
        branch_id=branch_id,
        track_laundry_cycle=False
    )
    db.add(snack)
    db.flush()
    
    # Link room to a location
    room_loc = Location(name="Room 202 Location", location_type="GUEST_ROOM", branch_id=branch_id, room_area="202", building="Main")
    db.add(room_loc)
    db.flush()
    room.inventory_location_id = room_loc.id
    
    # Add stock
    stock = LocationStock(location_id=room_loc.id, item_id=snack.id, quantity=10, branch_id=branch_id)
    db.add(stock)
    db.flush()

    # 4. Create Checkout Request
    checkout_req = CheckoutRequestModel(
        room_number="202",
        guest_name="Test Billing Guest",
        booking_id=booking.id,
        status="pending",
        branch_id=branch_id
    )
    db.add(checkout_req)
    db.flush()
    
    return {
        "booking": booking,
        "room": room,
        "snack": snack,
        "request": checkout_req
    }

class TestFullBillingCalculations:
    def test_room_gst_slab_12(self, authorized_client, db_session, test_branch):
        """Verify 12% GST for rooms below 7500."""
        # Seed 5000 price room
        data = seed_full_booking_data(db_session, test_branch, 5000.0)
        
        # Perform inventory check (Used 1 snack)
        payload = {
            "items": [
                {
                    "item_id": data["snack"].id,
                    "used_qty": 1,
                    "allocated_stock": 10,
                    "is_fixed_asset": False,
                    "is_returned": False
                }
            ]
        }
        res_check = authorized_client.post(f"/api/bill/checkout-request/{data['request'].id}/check-inventory", json=payload)
        assert res_check.status_code == 200
        
        # Get Bill Summary
        response = authorized_client.get(f"/api/bill/202")
        assert response.status_code == 200
        bill = response.json()
        
        # Calculations:
        # Room: 5000 * 2 nights = 10,000
        # GST (12%): 1,200
        # Consumable: 1 * 100 = 100
        # Consumable GST (5%): 5
        
        charges = bill["charges"]
        assert charges["room_charges"] == 10000.0
        assert charges["room_gst"] == 1200.0
        assert charges["consumables_charges"] == 100.0
        assert charges["consumables_gst"] == 5.0
        assert charges["total_gst"] == 1205.0
        assert charges["total_due"] == 10100.0

    def test_room_gst_slab_18(self, authorized_client, db_session, test_branch):
        """Verify 18% GST for rooms at or above 7500."""
        # Seed 8000 price room
        data = seed_full_booking_data(db_session, test_branch, 8000.0)
        
        # Get Bill Summary
        response = authorized_client.get(f"/api/bill/202")
        assert response.status_code == 200
        bill = response.json()
        
        charges = bill["charges"]
        # Room: 8000 * 2 nights = 16,000
        # GST (18%): 2,880
        assert charges["room_charges"] == 16000.0
        assert charges["room_gst"] == 2880.0
