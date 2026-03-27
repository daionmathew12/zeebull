
from app.database import SessionLocal
from app.api.checkout import get_checkout_request_inventory_details
from unittest.mock import MagicMock

db = SessionLocal()
request_id = 5

# Create a mock user
mock_user = MagicMock()
mock_user.name = "admin"

try:
    result = get_checkout_request_inventory_details(request_id, db, mock_user)
    print("Result:")
    import json
    # Use a custom encoder to handle objects if needed, but here it should be a dict
    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    import traceback
    traceback.print_exc()

db.close()
