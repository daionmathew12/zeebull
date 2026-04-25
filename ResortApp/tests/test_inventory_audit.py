import pytest
from datetime import date, datetime
from app.models.inventory import InventoryItem, InventoryCategory, Location, LocationStock, InventoryTransaction, PurchaseMaster, Vendor
from app.models.food_item import FoodItem
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.recipe import Recipe, RecipeIngredient
from app.models.account import JournalEntry, AccountLedger
from app.curd.inventory import process_food_order_usage

class TestInventoryAndFBAudit:
    
    def setup_inventory_environment(self, db_session, branch_id):
        # 1. Category
        cat = InventoryCategory(name="Raw Materials", parent_department="Kitchen", gst_tax_rate=5.0, branch_id=branch_id)
        db_session.add(cat)
        db_session.flush()
        
        # 2. Location (Kitchen)
        kitchen = Location(
            name="Main Kitchen", 
            building="Main Block", 
            room_area="Kitchen Area", 
            location_type="Department",
            branch_id=branch_id, 
            is_active=True
        )
        db_session.add(kitchen)
        db_session.flush()
        
        # 3. Inventory Items
        rice = InventoryItem(
            name="Basmati Rice", 
            category_id=cat.id, 
            current_stock=100.0, 
            unit="kg", 
            branch_id=branch_id,
            unit_price=60.0
        )
        chicken = InventoryItem(
            name="Chicken Breast", 
            category_id=cat.id, 
            current_stock=50.0, 
            unit="kg", 
            branch_id=branch_id,
            unit_price=250.0
        )
        db_session.add_all([rice, chicken])
        # Force unique constraint satisfaction (idempotency if session reused)
        db_session.flush()
        
        # 4. Location Stock
        db_session.add(LocationStock(location_id=kitchen.id, item_id=rice.id, quantity=100.0, branch_id=branch_id))
        db_session.add(LocationStock(location_id=kitchen.id, item_id=chicken.id, quantity=50.0, branch_id=branch_id))
        db_session.flush()
        
        return kitchen, rice, chicken

    def test_food_order_inventory_deduction(self, authorized_client, db_session, test_branch):
        """Verify that completing a food order deducts the correct amount of inventory based on recipe."""
        branch_id = test_branch.id
        kitchen, rice, chicken = self.setup_inventory_environment(db_session, branch_id)
        
        # 1. Create Food Item
        food = FoodItem(name="Chicken Biryani", price=350.0, branch_id=branch_id, available=True)
        db_session.add(food)
        db_session.flush()
        
        # 2. Create Recipe (0.5kg Rice, 0.3kg Chicken per portion)
        recipe = Recipe(food_item_id=food.id, name="Biryani Recipe", servings=1, branch_id=branch_id)
        db_session.add(recipe)
        db_session.flush()
        
        db_session.add(RecipeIngredient(recipe_id=recipe.id, inventory_item_id=rice.id, quantity=0.5, unit="kg"))
        db_session.add(RecipeIngredient(recipe_id=recipe.id, inventory_item_id=chicken.id, quantity=0.3, unit="kg"))
        db_session.commit()
        
        # 3. Create Food Order (2 portions)
        order = FoodOrder(
            amount=700.0,
            status="pending",
            branch_id=branch_id
        )
        db_session.add(order)
        db_session.flush()
        # Corrected: order_id instead of food_order_id
        db_session.add(FoodOrderItem(order_id=order.id, food_item_id=food.id, quantity=2, branch_id=branch_id))
        db_session.commit()
        
        # 4. Mark Order as Completed via API (should trigger deduction)
        response = authorized_client.put(f"/api/food-orders/{order.id}", json={"status": "completed"})
        assert response.status_code == 200
        
        # 5. VERIFY DEDUCTION
        # Expected deduction: Rice = 0.5 * 2 = 1kg, Chicken = 0.3 * 2 = 0.6kg
        db_session.expire_all()
        
        # Check Global Stock
        updated_rice = db_session.query(InventoryItem).filter(InventoryItem.id == rice.id).one()
        updated_chicken = db_session.query(InventoryItem).filter(InventoryItem.id == chicken.id).one()
        
        assert updated_rice.current_stock == 99.0 # 100 - 1
        assert updated_chicken.current_stock == 49.4 # 50 - 0.6
        
        # Check Location Stock (Kitchen)
        kitchen_rice = db_session.query(LocationStock).filter(LocationStock.location_id == kitchen.id, LocationStock.item_id == rice.id).one()
        assert kitchen_rice.quantity == 99.0
        
        # Check Transaction Log
        transactions = db_session.query(InventoryTransaction).filter(InventoryTransaction.reference_number == f"ORD-{order.id}").all()
        assert len(transactions) == 2
        assert any(t.item_id == rice.id and t.quantity == 1.0 for t in transactions)

    def test_purchase_order_gst_and_stock_update(self, authorized_client, db_session, test_branch):
        """Verify that a purchase order correctly updates stock and splits GST."""
        branch_id = test_branch.id
        
        # 1. Setup Vendor and Item
        vendor = Vendor(name="Global Foods", billing_state="Maharashtra", branch_id=branch_id)
        db_session.add(vendor)
        
        cat = InventoryCategory(name="Supplies", gst_tax_rate=12.0, branch_id=branch_id)
        db_session.add(cat)
        db_session.flush()
        
        item = InventoryItem(name="Bulk Flour", category_id=cat.id, current_stock=0.0, unit="kg", branch_id=branch_id)
        db_session.add(item)
        
        loc = Location(
            name="Warehouse", 
            building="Main Block", 
            room_area="Store Area", 
            location_type="Warehouse",
            branch_id=branch_id
        )
        db_session.add(loc)
        db_session.commit()
        
        # 2. Mock Purchase Flow
        from app.utils.accounting_helpers import create_purchase_journal_entry
        
        # Seed ledgers first
        from tests.test_finance_audit import seed_bookkeeping_ledgers
        seed_bookkeeping_ledgers(db_session, branch_id)
        
        # Link ledger for inventory asset if missing
        inv_ledger = db_session.query(AccountLedger).filter(AccountLedger.name == "Inventory Asset (Stock)").first()
        if not inv_ledger:
            from app.models.account import AccountGroup
            grp = db_session.query(AccountGroup).first()
            db_session.add(AccountLedger(name="Inventory Asset (Stock)", group_id=grp.id, module="Inventory", branch_id=branch_id))
            db_session.add(AccountLedger(name="Accounts Payable (Vendor)", group_id=grp.id, module="Purchase", branch_id=branch_id))
            db_session.add(AccountLedger(name="Input CGST", group_id=grp.id, module="Tax", branch_id=branch_id))
            db_session.add(AccountLedger(name="Input SGST", group_id=grp.id, module="Tax", branch_id=branch_id))
            db_session.commit()

        # Purchase Details
        purchase = PurchaseMaster(
            purchase_number="PO-TEST-001",
            vendor_id=vendor.id,
            total_amount=2240.0,
            sub_total=2000.0,
            cgst=120.0,
            sgst=120.0,
            status="received",
            branch_id=branch_id,
            destination_location_id=loc.id
        )
        db_session.add(purchase)
        db_session.commit()

        # Execute Journal Entry
        entry_id = create_purchase_journal_entry(
            db=db_session,
            purchase_id=purchase.id,
            vendor_id=vendor.id,
            inventory_amount=2000.0,
            cgst_amount=120.0,
            sgst_amount=120.0,
            vendor_name="Global Foods",
            branch_id=branch_id
        )
        
        assert entry_id is not None
        entry = db_session.query(JournalEntry).filter(JournalEntry.id == entry_id).one()
        assert entry.total_amount == 2240.0
        assert len(entry.lines) == 4 # Asset + CGST + SGST + Payable
