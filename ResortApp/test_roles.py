import requests
import json
import sys

# Get token from the test file earlier generated
with open('TEST_TOKEN.txt', 'r') as f:
    TOKEN = f.read().strip()

BASE_URL = 'http://localhost:8011'
HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'X-Branch-ID': '1',
    'Content-Type': 'application/json'
}

print("1. Testing Create Duplicate 'Manager' Role...")
data = {
    "name": "Manager",
    "permissions": json.dumps(["Dashboard", "Account", "Bookings", "Rooms"])
}

res = requests.post(f"{BASE_URL}/api/roles", headers=HEADERS, json=data)
if res.status_code == 400:
    print(f"✅ SUCCESS: Server correctly blocked duplicate role creation: {res.json()['detail']}")
else:
    print(f"❌ FAIL: Expected 400, got {res.status_code}. Response: {res.text}")
    sys.exit(1)

print("\n2. Getting existing role list to find non-Manager role ID...")
res_roles = requests.get(f"{BASE_URL}/api/roles", headers=HEADERS)
roles = res_roles.json()
guest_role = next((r for r in roles if r['name'].lower() != 'manager'), None)

if guest_role:
    print(f"Testing Update Role ID {guest_role['id']} ('{guest_role['name']}') to 'Manager'...")
    update_data = {
        "name": "Manager",
        "permissions": guest_role['permissions']
    }
    res_update = requests.put(f"{BASE_URL}/api/roles/{guest_role['id']}", headers=HEADERS, json=update_data)
    
    if res_update.status_code == 400:
        print(f"✅ SUCCESS: Server correctly blocked duplicate role rename: {res_update.json()['detail']}")
    else:
        print(f"❌ FAIL: Expected 400, got {res_update.status_code}. Response: {res_update.text}")
        sys.exit(1)
else:
    print("Could not find another role to test rename constraint.")
    
print("\nAll verification tests passed!")
