import requests

BASE_URL = "http://127.0.0.1:8011/api"

def test_room_fetching():
    # Login to get a token (assuming superadmin or manager)
    login_data = {
        "email": "admin@zeebull.com",
        "password": "password123"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if resp.statusCode != 200:
            print(f"Login failed: {resp.text}")
            # Try alternate credentials if needed
            return
        token = resp.json()["access_token"]
    except:
        # If login fails, try with a manual token if we had one, 
        # or just assume the backend is open for now (unlikely)
        print("Login failed, trying without token (will likely fail 401)")
        token = ""

    headers = {"Authorization": f"Bearer {token}"}

    # Test Branch 1, Type 1
    print("\nTesting Branch 1, Type 1:")
    r1 = requests.get(f"{BASE_URL}/rooms", params={"branch_id": 1, "room_type_id": 1, "status": "Available"}, headers=headers)
    if r1.status_code == 200:
        rooms = r1.json()
        print(f"Rooms found: {[r['number'] for r in rooms]}")
    else:
        print(f"Error {r1.status_code}: {r1.text}")

    # Test Branch 2, Type 1
    print("\nTesting Branch 2, Type 1:")
    r2 = requests.get(f"{BASE_URL}/rooms", params={"branch_id": 2, "room_type_id": 1, "status": "Available"}, headers=headers)
    if r2.status_code == 200:
        rooms = r2.json()
        print(f"Rooms found: {[r['number'] for r in rooms]}")
    else:
        print(f"Error {r2.status_code}: {r2.text}")

if __name__ == "__main__":
    test_room_fetching()
