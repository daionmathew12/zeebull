from fastapi.testclient import TestClient
from main import app
from app.utils.auth import get_current_user

# Mock User
class MockUser:
    id = 1
    name = "admin"
    branch_id = 2
    is_superadmin = False

app.dependency_overrides[get_current_user] = lambda: MockUser()

client = TestClient(app)
response = client.get("/api/bookings/details/BK-2-000006?is_package=false")

if response.status_code == 200:
    data = response.json()
    print(f"Inventory: {len(data.get('inventory_usage', []))}")
    print(f"Food Orders: {len(data.get('food_orders', []))}")
    print(f"Service Requests: {len(data.get('service_requests', []))}")
else:
    print(f"Error: {response.text}")
