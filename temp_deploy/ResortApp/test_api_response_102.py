from fastapi.testclient import TestClient
from app.main import app
from app.api.auth import get_current_active_user
from app.models.user import User

# Override auth to bypass login
def override_get_current_active_user():
    return User(id=1, username="admin", role="admin")

app.dependency_overrides[get_current_active_user] = override_get_current_active_user

client = TestClient(app)

print("Fetching items for Location 19 (Room 102)...")
response = client.get("/api/inventory/locations/19/items")

if response.status_code == 200:
    data = response.json()
    print(f"Total Items: {len(data)}")
    
    found_walkie = False
    for item in data:
        if "Walkie" in item.get("item_name", "") or "Walkie" in str(item):
            print("FOUND Walkie Talkie!")
            print(f"  Type: {item.get('type')}")
            print(f"  Name: {item.get('item_name')}")
            found_walkie = True
            
    if not found_walkie:
        print("Walkie Talkie NOT FOUND in response.")
        
else:
    print(f"Error: {response.status_code}")
    print(response.text)
