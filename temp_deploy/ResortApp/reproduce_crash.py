
import sys
import os
# Add project root to path
sys.path.append(os.getcwd())

from unittest.mock import MagicMock, patch
from datetime import datetime

# Set up mocks BEFORE importing app.api.checkout
sys.modules['app.main'] = MagicMock()
sys.modules['app.curd.account'] = MagicMock()
sys.modules['app.utils.accounting_helpers'] = MagicMock()
sys.modules['app.utils.pdf_generator'] = MagicMock()
sys.modules['app.utils.email'] = MagicMock()

# Import the function to test
from app.api.checkout import handleCompleteCheckoutRequest
from app.schemas.checkout import InventoryCheckRequest, InventoryCheckItem, AssetDamageItem
from app.models.inventory import InventoryItem, LocationStock, AssetRegistry

# Mock DB Session
mock_db = MagicMock()

# Mock User
mock_user = MagicMock()
mock_user.id = 1

# Mock Request Payload
# Consumable: Milk (Used 1) - Should deduct global stock
item1 = InventoryCheckItem(
    item_id=101,
    item_name="Milk",
    used_qty=1,
    missing_qty=0,
    damage_qty=0,
    is_rentable=False,
    is_fixed_asset=False
)

# Asset: TV (Rented) - Marked Waste, but NO location selected (simulating user error)
asset1 = AssetDamageItem(
    item_id=202,
    item_name="Tv (Rented)",
    is_damaged=True,
    is_waste=True,
    waste_location_id=None, # USER DID NOT SELECT LOCATION
    request_replacement=False,
    replacement_cost=1000.0,
    item_id_or_registry_id=1, # Mock specific asset
    asset_registry_id=1
)

payload = InventoryCheckRequest(
    items=[item1],
    asset_damages=[asset1],
    inventory_notes="Test checkout"
)

# Mock InventoryItem query
mock_inv_item = MagicMock()
mock_inv_item.id = 101
mock_inv_item.current_stock = 100
mock_inv_item.item_name = "Milk"

mock_asset_item = MagicMock()
mock_asset_item.id = 202
mock_asset_item.current_stock = 10
mock_asset_item.item_name = "Tv (Rented)"

def mock_query_side_effect(model):
    query_mock = MagicMock()
    if model == InventoryItem:
        # Return different mock based on subsequent filter... tricky to mock exact chain
        # so we'll just make filter().first() return something generic or specific if we can
        return query_mock
    return query_mock

mock_db.query.side_effect = mock_query_side_effect

# Basic mock for filter().first()
mock_db.query.return_value.filter.return_value.first.return_value = mock_inv_item

# We need more specific mocking for the loop
# We can patch the internal query usage or simplfy the test to just run and see if it crashes on None access

print("Running Checkout Crash Simulation...")
try:
    # Run the function
    # Note: request_id is integer
    handleCompleteCheckoutRequest(
        request_id=999,
        payload=payload,
        db=mock_db,
        current_user=mock_user
    )
    print("Execution completed successfully (No Crash).")
except Exception as e:
    print(f"CRASH DETECTED: {e}")
    import traceback
    traceback.print_exc()
