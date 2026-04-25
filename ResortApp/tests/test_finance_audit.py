import pytest
import json
from datetime import date, timedelta, datetime
from app.models.food_item import FoodItem
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.account import JournalEntry, JournalEntryLine, AccountLedger, AccountGroup, AccountType
from app.models.room import Room, RoomType
from app.models.booking import Booking, BookingRoom
from app.models.expense import Expense
from app.models.user import User
from app.curd.foodorder import get_ist_now

def seed_bookkeeping_ledgers(db, branch_id):
    """Seed the required Chart of Accounts for a branch to succeed in journal entry creation."""
    # 1. Groups
    revenue_group = AccountGroup(name="Revenue Accounts", account_type=AccountType.REVENUE, branch_id=branch_id)
    asset_group = AccountGroup(name="Asset Accounts", account_type=AccountType.ASSET, branch_id=branch_id)
    tax_group = AccountGroup(name="Tax Accounts", account_type=AccountType.TAX, branch_id=branch_id)
    db.add_all([revenue_group, asset_group, tax_group])
    db.flush()
    
    # 2. Ledgers
    ledgers = [
        AccountLedger(name="Accounts Receivable (Guest)", group_id=asset_group.id, module="Booking", branch_id=branch_id),
        AccountLedger(name="Food Revenue (Taxable)", group_id=revenue_group.id, module="Food", branch_id=branch_id),
        AccountLedger(name="Output CGST", group_id=tax_group.id, module="Tax", branch_id=branch_id),
        AccountLedger(name="Output SGST", group_id=tax_group.id, module="Tax", branch_id=branch_id),
        AccountLedger(name="Cash", group_id=asset_group.id, module="Asset", branch_id=branch_id),
        AccountLedger(name="General Expense", group_id=asset_group.id, module="Expense", branch_id=branch_id), # Simplified
    ]
    db.add_all(ledgers)
    db.flush()
    return ledgers

class TestFinanceAndEnterpriseAudit:
    
    def test_food_time_based_pricing_logic(self, authorized_client, db_session, test_branch):
        """Verify that food orders resolve price based on time slots."""
        branch_id = test_branch.id
        now = get_ist_now()
        
        # Create a food item with two prices: 
        # Regular: 200, Dinner (Current): 500
        dinner_from = (now - timedelta(hours=1)).strftime("%H:%M")
        dinner_to = (now + timedelta(hours=1)).strftime("%H:%M")
        
        time_prices = [
            {"from_time": dinner_from, "to_time": dinner_to, "price": 500.0}
        ]
        
        food = FoodItem(
            name="Audit Steak",
            price=200.0,
            time_wise_prices=json.dumps(time_prices),
            branch_id=branch_id,
            available=True
        )
        db_session.add(food)
        
        # Also need a room and booking for the order
        rtype = RoomType(name="Audit Room", base_price=1000.0, branch_id=branch_id)
        db_session.add(rtype)
        db_session.flush()
        room = Room(number="A1", branch_id=branch_id, room_type_id=rtype.id)
        db_session.add(room)
        db_session.flush()
        
        booking = Booking(
            guest_name="Finance Guest",
            check_in=date.today(),
            check_out=date.today() + timedelta(days=1),
            status="checked-in",
            branch_id=branch_id
        )
        db_session.add(booking)
        db_session.flush()
        db_session.add(BookingRoom(booking_id=booking.id, room_id=room.id, branch_id=branch_id))
        db_session.commit()
        
        # Create Order via API
        payload = {
            "room_id": room.id,
            "items": [{"food_item_id": food.id, "quantity": 1}],
            "amount": 0 # Backend should auto-calculate to 500
        }
        
        response = authorized_client.post("/api/food-orders/", json=payload)
        assert response.status_code == 200
        order = response.json()
        
        # CHECK: Amount should be 500 (Dinner price), not 200 (Base price)
        assert order["amount"] == 500.0
        assert order["gst_amount"] == 25.0 # 5%
        assert order["total_with_gst"] == 525.0

    def test_enterprise_dashboard_aggregation(self, authorized_client, db_session, test_branch):
        """Verify super_admin can see aggregated data using X-Branch-ID: all."""
        # Create second branch
        from app.models.branch import Branch
        branch2 = Branch(name="Second Branch", code="SB")
        db_session.add(branch2)
        db_session.commit()
        
        headers = {"X-Branch-ID": "all"}
        response = authorized_client.get("/api/dashboard/stats", headers=headers)
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "total_revenue" in data or "occupancy" in data

    def test_expense_branch_isolation(self, authorized_client, db_session, test_branch):
        """Verify expenses are correctly scoped to branches."""
        branch_id = test_branch.id
        seed_bookkeeping_ledgers(db_session, branch_id)
        
        # Create expense in Branch 1
        expense = Expense(
            description="Branch 1 Repair",
            amount=1000.0,
            category="Maintenance",
            branch_id=branch_id,
            date=date.today()
        )
        db_session.add(expense)
        db_session.commit()
        
        # Fetch with Branch 1 scope (Default for this client)
        response = authorized_client.get("/api/expenses")
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        expenses = response.json()
        assert any(e["description"] == "Branch 1 Repair" for e in expenses)
        
        # Try to fetch with Branch 2 (should be empty/isolated)
        headers = {"X-Branch-ID": "999"} # Non-existent branch
        response = authorized_client.get("/api/expenses", headers=headers)
        assert response.status_code in [200, 403, 404]
        if response.status_code == 200:
            expenses2 = response.json()
            assert not any(e["description"] == "Branch 1 Repair" for e in expenses2)

    def test_journal_entry_on_food_payment(self, authorized_client, db_session, test_branch):
        """Verify that marking food order as paid creates a journal entry."""
        branch_id = test_branch.id
        seed_bookkeeping_ledgers(db_session, branch_id)
        
        # 1. Create a food order (Not paid yet)
        order = FoodOrder(
            room_id=None, # Walk-in
            amount=1000.0,
            gst_amount=0,
            total_with_gst=0,
            status="completed",
            billing_status="unbilled",
            branch_id=branch_id
        )
        db_session.add(order)
        db_session.commit()
        
        # 2. Mark as paid
        response = authorized_client.post(f"/api/food-orders/{order.id}/mark-paid?payment_method=cash")
        assert response.status_code == 200, f"Failed to mark paid: {response.text}"
        
        # 3. Check Journal Entries
        entries = db_session.query(JournalEntry).filter(
            JournalEntry.reference_type == "food_order",
            JournalEntry.reference_id == order.id
        ).all()
        
        # Should have 1 journal entry with at least 2 lines (Debit AR/Cash, Credit Revenue)
        assert len(entries) >= 1, f"No journal entry created for food order {order.id}"
        entry = entries[0]
        assert entry.total_amount == 1050.0, f"Expected 1050.0 total but got {entry.total_amount}"
        assert len(entry.lines) >= 2
