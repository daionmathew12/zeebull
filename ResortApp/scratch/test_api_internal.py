from fastapi.testclient import TestClient
from main import app
from app.utils.auth import get_db, get_current_user
from app.models.user import User
from app.database import SessionLocal

# Mock User
class MockUser:
    id = 1
    name = "admin"
    branch_id = 2 # Setting to 2 to match Booking 6
    is_superadmin = False

def get_mock_user():
    return MockUser()

# Override dependencies
app.dependency_overrides[get_current_user] = get_mock_user

client = TestClient(app)

response = client.get("/api/bookings/details/BK-2-000006?is_package=false")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    inventory = data.get("inventory_usage", [])
    print(f"Inventory Count: {len(inventory)}")
    for item in inventory:
        print(f" - {item['item_name']} ({item['notes']})")
else:
    print(f"Error: {response.text}")
