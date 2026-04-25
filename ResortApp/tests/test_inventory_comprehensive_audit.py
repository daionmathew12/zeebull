import pytest
from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import Optional
from fastapi import Header
from app.models.inventory import (
    InventoryCategory, InventoryItem, Vendor, PurchaseMaster, PurchaseDetail, 
    InventoryTransaction, StockRequisition, StockRequisitionDetail, 
    StockIssue, StockIssueDetail, WasteLog, Location, LocationStock, AssetMapping,
    InterBranchTransfer
)
from app.models.branch import Branch
from app.models.food_item import FoodItem
from app.models.food_category import FoodCategory
from app.models.recipe import Recipe, RecipeIngredient
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.utils.auth import get_branch_id as get_branch_id_auth
from app.utils.branch_scope import get_branch_id as get_branch_id_scope
from main import app

class TestInventoryComprehensiveAudit:

    @pytest.fixture(autouse=True)
    def fix_all_branch_contexts(self, authorized_client, test_branch, mock_superadmin, db_session):
        """
        1. Restore real get_branch_id logic by removing ALL conftest overrides.
        2. Set mock user's branch to the test branch to satisfy logic that falls back to user branch.
        """
        # Remove the overrides from conftest to use real header/user logic
        app.dependency_overrides.pop(get_branch_id_scope, None)
        app.dependency_overrides.pop(get_branch_id_auth, None)
        
        # Sync user branch in DB
        mock_superadmin.branch_id = test_branch.id
        db_session.add(mock_superadmin)
        db_session.commit()
        
        yield
        
        # Restore the conftest overrides (None) to avoid breaking other tests
        app.dependency_overrides[get_branch_id_scope] = lambda: None
        app.dependency_overrides[get_branch_id_auth] = lambda: None

    def setup_inventory_locations(self, db_session, branch_id):
        warehouse = Location(
            name="Main Warehouse", 
            location_type="WAREHOUSE", 
            branch_id=branch_id,
            building="Main Block",
            room_area="Warehouse A"
        )
        kitchen = Location(
            name="Main Kitchen", 
            location_type="DEPARTMENT", 
            branch_id=branch_id,
            building="Utility Block",
            room_area="Kitchen Area"
        )
        room_loc = Location(
            name="Room 101", 
            location_type="GUEST_ROOM", 
            branch_id=branch_id,
            building="Guest Block",
            room_area="Room 101"
        )
        db_session.add_all([warehouse, kitchen, room_loc])
        db_session.commit()
        return warehouse, kitchen, room_loc

    def test_inventory_procurement_lifecycle(self, authorized_client, db_session, test_branch):
        """Audit the Purchase Lifecycle: PO -> Received -> Stock & Transaction Verification."""
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        wh, kitchen, _ = self.setup_inventory_locations(db_session, branch_id)
        
        # 1. Setup Master Data
        cat = InventoryCategory(name="Supplies", branch_id=branch_id)
        db_session.add(cat)
        db_session.flush()
        
        vendor = Vendor(name="Global Supplies", branch_id=branch_id)
        db_session.add(vendor)
        db_session.flush()
        
        item = InventoryItem(
            name="Sugar", item_code="SUG-PROC-01", category_id=cat.id, 
            unit="kg", unit_price=50.0, current_stock=0.0,
            branch_id=branch_id
        )
        db_session.add(item)
        db_session.commit()
        
        # 2. Create Purchase Order (Pending)
        po_payload = {
            "purchase_number": "PO-PROC-" + str(datetime.now().timestamp()),
            "vendor_id": vendor.id,
            "purchase_date": str(date.today()),
            "status": "pending",
            "destination_location_id": wh.id,
            "details": [
                {
                    "item_id": item.id,
                    "quantity": 100,
                    "unit": "kg",
                    "unit_price": 60.0,
                    "gst_rate": 18
                }
            ]
        }
        response = authorized_client.post("/api/inventory/purchases", json=po_payload, headers=headers)
        if response.status_code != 200:
            print(f"PO creation failed: {response.text}")
        assert response.status_code == 200
        po_id = response.json()["id"]
        
        # 3. Receive Purchase (Status -> received)
        response = authorized_client.patch(f"/api/inventory/purchases/{po_id}/status?status=received", headers=headers)
        assert response.status_code == 200
        
        # 4. Verify Stock at Location
        db_session.expire_all()
        loc_stock = db_session.query(LocationStock).filter(
            LocationStock.location_id == wh.id, 
            LocationStock.item_id == item.id
        ).first()
        assert loc_stock is not None
        assert float(loc_stock.quantity) == 100.0
        
        # 5. Verify Weighted Average Cost (WAC)
        updated_item = db_session.query(InventoryItem).filter(InventoryItem.id == item.id).first()
        assert float(updated_item.unit_price) == 60.0
        assert float(updated_item.current_stock) == 100.0

    def test_stock_issue_and_requisition_flow(self, authorized_client, db_session, test_branch):
        """Audit internal stock movement: Requisition -> Issue -> Verification."""
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        wh, kitchen, _ = self.setup_inventory_locations(db_session, branch_id)
        
        # 1. Setup Initial Stock (100 in WH)
        cat = InventoryCategory(name="Kitchen Assets", branch_id=branch_id)
        db_session.add(cat)
        db_session.flush()
        
        item = InventoryItem(
            name="Chef Knife", category_id=cat.id, unit="pcs", 
            current_stock=100.0, branch_id=branch_id
        )
        db_session.add(item)
        db_session.flush()
        
        wh_stock = LocationStock(location_id=wh.id, item_id=item.id, quantity=100.0, branch_id=branch_id)
        db_session.add(wh_stock)
        db_session.commit()
        
        # 2. Create Requisition
        req_payload = {
            "destination_department": "Main Kitchen",
            "date_needed": str(date.today()),
            "details": [{"item_id": item.id, "requested_quantity": 5, "unit": "pcs"}]
        }
        response = authorized_client.post("/api/inventory/requisitions", json=req_payload, headers=headers)
        if response.status_code != 200:
            print(f"Requisition failed: {response.text}")
        assert response.status_code == 200
        req_id = response.json()["id"]
        
        # 3. Issue Stock from WH to Kitchen
        issue_payload = {
            "requisition_id": req_id,
            "source_location_id": wh.id,
            "destination_location_id": kitchen.id,
            "details": [{"item_id": item.id, "issued_quantity": 5, "unit": "pcs"}]
        }
        response = authorized_client.post("/api/inventory/issues", json=issue_payload, headers=headers)
        if response.status_code != 200:
            print(f"Issue failed: {response.text}")
        assert response.status_code == 200
        
        # 4. Verify Stock Movements
        db_session.expire_all()
        wh_stock_new = db_session.query(LocationStock).filter(LocationStock.location_id == wh.id, LocationStock.item_id == item.id).first()
        assert float(wh_stock_new.quantity) == 95.0
        
        kitchen_stock = db_session.query(LocationStock).filter(LocationStock.location_id == kitchen.id, LocationStock.item_id == item.id).first()
        assert float(kitchen_stock.quantity) == 5.0

    def test_waste_log_deduction(self, authorized_client, db_session, test_branch):
        """Audit spoilage/waste deduction logic."""
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        wh, _, _ = self.setup_inventory_locations(db_session, branch_id)
        
        cat = InventoryCategory(name="Perishables", branch_id=branch_id)
        db_session.add(cat)
        db_session.flush()
        
        item = InventoryItem(
            name="Milk", unit="L", current_stock=10.0, 
            category_id=cat.id, branch_id=branch_id
        )
        db_session.add(item)
        db_session.flush()
        
        wh_stock = LocationStock(location_id=wh.id, item_id=item.id, quantity=10.0, branch_id=branch_id)
        db_session.add(wh_stock)
        db_session.commit()
        
        # 1. Report Waste (multipart/form-data)
        waste_data = {
            "item_id": str(item.id),
            "location_id": str(wh.id),
            "quantity": "2.0",
            "unit": "L",
            "reason_code": "SPOILED",
            "notes": "Fridge failed"
        }
        response = authorized_client.post("/api/inventory/waste-logs", data=waste_data, headers=headers)
        assert response.status_code == 200
        
        # 2. Verify Deductions
        db_session.expire_all()
        updated_item = db_session.query(InventoryItem).filter(InventoryItem.id == item.id).first()
        assert float(updated_item.current_stock) == 8.0

    def test_inter_branch_transfer_lifecycle(self, authorized_client, db_session, test_branch):
        """Audit cross-branch stock movement."""
        # Source Branch: test_branch (Branch A)
        branch_a_id = test_branch.id
        headers_a = {"X-Branch-ID": str(branch_a_id)}
        wh_a, _, _ = self.setup_inventory_locations(db_session, branch_a_id)
        
        # Destination Branch: (Branch B)
        branch_b = Branch(name="Mountain View Branch", code="B" + str(datetime.now().timestamp())[-5:], is_active=True)
        db_session.add(branch_b)
        db_session.flush()
        branch_b_id = branch_b.id
        headers_b = {"X-Branch-ID": str(branch_b_id)}
        wh_b = Location(
            name="Mountain Warehouse", location_type="WAREHOUSE", branch_id=branch_b_id,
            building="North Block", room_area="Basement 1"
        )
        db_session.add(wh_b)
        db_session.flush()
        db_session.commit()
        
        # 1. Setup Item in Branch A
        cat = InventoryCategory(name="Branch Assets", branch_id=branch_a_id)
        db_session.add(cat)
        db_session.flush()
        item = InventoryItem(
            name="Extra Bed", unit="pcs", current_stock=50.0, 
            category_id=cat.id, branch_id=branch_a_id
        )
        db_session.add(item)
        db_session.flush()
        wh_a_stock = LocationStock(location_id=wh_a.id, item_id=item.id, quantity=50.0, branch_id=branch_a_id)
        db_session.add(wh_a_stock)
        db_session.commit()
        
        # 2. Create Transfer (Branch A -> Branch B)
        transfer_payload = {
            "item_id": item.id,
            "quantity": 10,
            "destination_branch_id": branch_b_id,
            "source_location_id": wh_a.id,
            "notes": "Moving stock"
        }
        response = authorized_client.post("/api/inventory/transfers", json=transfer_payload, headers=headers_a)
        if response.status_code != 200:
            print(f"Transfer creation failed: {response.text}")
        assert response.status_code == 200
        trf_id = response.json()["id"]
        
        # 3. Mark as In Transit (Source branch scope)
        response = authorized_client.patch(f"/api/inventory/transfers/{trf_id}/status?status=in_transit", headers=headers_a)
        assert response.status_code == 200
        
        db_session.expire_all()
        wh_a_stock_new = db_session.query(LocationStock).filter(LocationStock.location_id == wh_a.id, LocationStock.item_id == item.id).first()
        assert float(wh_a_stock_new.quantity) == 40.0
        
        # 4. Mark as Received (Destination branch scope)
        response = authorized_client.patch(f"/api/inventory/transfers/{trf_id}/status?status=received&location_id={wh_b.id}", headers=headers_b)
        if response.status_code != 200:
            print(f"Transfer receipt failed: {response.text}")
        assert response.status_code == 200
        
        db_session.expire_all()
        wh_b_stock = db_session.query(LocationStock).filter(LocationStock.location_id == wh_b.id, LocationStock.item_id == item.id).first()
        assert float(wh_b_stock.quantity) == 10.0

    def test_recipe_order_consumption(self, authorized_client, db_session, test_branch):
        """Audit that completing a food order deducts ingredients per recipe."""
        branch_id = test_branch.id
        headers = {"X-Branch-ID": str(branch_id)}
        _, kitchen, _ = self.setup_inventory_locations(db_session, branch_id)
        kitchen.name = "Main Kitchen"
        db_session.commit()
        
        # 1. Setup Ingredient Stock (Flour: 10kg in Kitchen)
        cat = InventoryCategory(name="Bakery Raw", branch_id=branch_id)
        db_session.add(cat)
        db_session.flush()
        
        ing_item = InventoryItem(
            name="Flour", unit="kg", current_stock=10.0, 
            unit_price=40.0, category_id=cat.id, branch_id=branch_id
        )
        db_session.add(ing_item)
        db_session.flush()
        kit_stock = LocationStock(location_id=kitchen.id, item_id=ing_item.id, quantity=10.0, branch_id=branch_id)
        db_session.add(kit_stock)
        
        # 2. Setup Food Item & Recipe (1 Cake uses 0.5kg Flour)
        f_cat = FoodCategory(name="Bakery Items", branch_id=branch_id)
        db_session.add(f_cat)
        db_session.flush()
        food = FoodItem(name="Wedding Cake", category_id=f_cat.id, price=500.0, branch_id=branch_id)
        db_session.add(food)
        db_session.flush()
        recipe = Recipe(food_item_id=food.id, name="Wedding Cake Recipe", servings=1, branch_id=branch_id)
        db_session.add(recipe)
        db_session.flush()
        ri = RecipeIngredient(recipe_id=recipe.id, inventory_item_id=ing_item.id, quantity=0.5, unit="kg")
        db_session.add(ri)
        
        # 3. Create Food Order (2 Cakes)
        order = FoodOrder(
            branch_id=branch_id, status="pending", amount=1000.0, 
            total_with_gst=1050.0, order_type="dine_in"
        )
        db_session.add(order)
        db_session.flush()
        oi = FoodOrderItem(order_id=order.id, food_item_id=food.id, quantity=2, branch_id=branch_id)
        db_session.add(oi)
        db_session.commit()
        
        # 4. Complete Order (using PUT as PATCH /status doesn't exist)
        payload = {"status": "completed"}
        response = authorized_client.put(f"/api/food-orders/{order.id}", json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Order completion failed: {response.text}")
        assert response.status_code == 200
        
        # 5. Verify Stock Deduction (2 Cakes * 0.5kg = 1kg deducted)
        db_session.expire_all()
        kit_stock_new = db_session.query(LocationStock).filter(LocationStock.location_id == kitchen.id, LocationStock.item_id == ing_item.id).first()
        assert float(kit_stock_new.quantity) == 9.0
        
        updated_ing = db_session.query(InventoryItem).filter(InventoryItem.id == ing_item.id).first()
        assert float(updated_ing.current_stock) == 9.0
