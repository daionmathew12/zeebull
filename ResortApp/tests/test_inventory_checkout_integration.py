"""
test_inventory_checkout_integration.py — Tests for inventory side-effects during checkout.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.branch import Branch
from app.models.room import Room
from app.models.inventory import InventoryItem, LocationStock, Location, LaundryLog, InventoryCategory
from app.models.checkout import CheckoutRequest as CheckoutRequestModel

def seed_checkout_data(db: Session, branch: Branch):
    """Seed data for inventory checkout tests."""
    branch_id = branch.id
    # 1. Create a category
    category = InventoryCategory(name="Housekeeping", branch_id=branch_id)
    db.add(category)
    db.flush()

    # 2. Create Items
    # Consumable (Soap)
    soap = InventoryItem(
        name="Soap Bar",
        category_id=category.id,
        is_sellable_to_guest=True,
        branch_id=branch_id
    )
    # Linen (Towel) - Laundry Tracked
    towel = InventoryItem(
        name="Bath Towel",
        category_id=category.id,
        track_laundry_cycle=True,
        branch_id=branch_id
    )
    db.add_all([soap, towel])
    db.flush()

    # 3. Create Locations
    warehouse = Location(name="Main Warehouse", location_type="WAREHOUSE", branch_id=branch_id, building="Main", room_area="Warehouse")
    laundry = Location(name="Laundry", location_type="LAUNDRY", branch_id=branch_id, building="Main", room_area="Laundry")
    room_loc = Location(name="Room 101 Location", location_type="GUEST_ROOM", branch_id=branch_id, building="Main", room_area="101")
    db.add_all([warehouse, laundry, room_loc])
    db.flush()

    # 4. Set room
    room = Room(number="101", branch_id=branch_id, inventory_location_id=room_loc.id)
    db.add(room)
    db.flush()

    # 5. Add Stock to Room
    soap_stock = LocationStock(location_id=room_loc.id, item_id=soap.id, quantity=5, branch_id=branch_id)
    towel_stock = LocationStock(location_id=room_loc.id, item_id=towel.id, quantity=2, branch_id=branch_id)
    db.add_all([soap_stock, towel_stock])
    db.flush()

    # 6. Create Checkout Request
    checkout_req = CheckoutRequestModel(
        room_number="101",
        guest_name="Test Guest",
        status="pending",
        branch_id=branch_id
    )
    db.add(checkout_req)
    db.flush()

    return {
        "room": room,
        "soap": soap,
        "towel": towel,
        "request": checkout_req,
        "warehouse": warehouse,
        "laundry": laundry
    }

class TestInventoryCheckoutIntegration:
    def test_consumable_deduction(self, authorized_client, db_session, test_branch):
        """Verify that used consumables are deducted from room stock."""
        data = seed_checkout_data(db_session, test_branch)
        req_id = data["request"].id
        
        # Submit inventory check
        # Case: Used 2 soaps
        payload = {
            "inventory_notes": "Tested check",
            "items": [
                {
                    "item_id": data["soap"].id,
                    "used_qty": 2,
                    "allocated_stock": 5,
                    "is_fixed_asset": False,
                    "is_returned": False
                }
            ]
        }
        
        response = authorized_client.post(f"/api/bill/checkout-request/{req_id}/check-inventory", json=payload)
        assert response.status_code == 200
        
        # Verify stock deduction (5 - 2 = 3)
        db_session.expire_all()
        stock = db_session.query(LocationStock).filter(
            LocationStock.location_id == data["room"].inventory_location_id,
            LocationStock.item_id == data["soap"].id
        ).first()
        assert stock.quantity == 3.0

    def test_laundry_cycle_movement(self, authorized_client, db_session, test_branch):
        """Verify that laundry items are moved to laundry location and logged."""
        # Seeding
        data = seed_checkout_data(db_session, test_branch)
        req_id = data["request"].id
        
        # Room has 2 towels. Guest didn't 'use' them (meaning consume), but we mark as laundry.
        payload = {
            "items": [
                {
                    "item_id": data["towel"].id,
                    "used_qty": 0,
                    "allocated_stock": 2,
                    "is_fixed_asset": True,
                    "is_laundry": True,
                    "is_returned": True, # Moving out
                    "return_location_id": data["laundry"].id
                }
            ]
        }
        
        response = authorized_client.post(f"/api/bill/checkout-request/{req_id}/check-inventory", json=payload)
        assert response.status_code == 200
        
        # Verify room stock is now 0 (moved out)
        db_session.expire_all()
        room_stock = db_session.query(LocationStock).filter(
            LocationStock.location_id == data["room"].inventory_location_id,
            LocationStock.item_id == data["towel"].id
        ).first()
        assert room_stock.quantity == 0.0
        
        # Verify laundry stock increased
        laundry_stock = db_session.query(LocationStock).filter(
            LocationStock.location_id == data["laundry"].id,
            LocationStock.item_id == data["towel"].id
        ).first()
        assert laundry_stock.quantity == 2.0
        
        # Verify LaundryLog entry
        log = db_session.query(LaundryLog).filter(LaundryLog.room_number == "101").first()
        assert log is not None
        assert log.quantity == 2.0
        assert log.status == "Incomplete Washing"
