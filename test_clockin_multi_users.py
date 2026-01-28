import requests
import json

# Get a valid token first - let's try a different user
login_url = "https://teqmates.com/orchidapi/api/auth/login"

# Try different credentials
test_users = [
    {"email": "alphi@gmail.com", "password": "admin123"},
    {"email": "admin@orchid.com", "password": "admin123"},
    {"email": "manager@orchid.com", "password": "admin123"},
]

token = None
for user in test_users:
    print(f"Trying login with {user['email']}...")
    try:
        response = requests.post(login_url, json=user)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✓ Login successful! Got token")
            break
        else:
            print(f"✗ Failed: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"✗ Exception: {e}")

if token:
    # Try clock-in
    print("\n--- Testing Clock-In ---")
    clockin_url = "https://teqmates.com/orchidapi/api/attendance/clock-in"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "employee_id": 31,
        "location": "Test Script"
    }
    
    try:
        response = requests.post(clockin_url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("\nCould not get a valid token with any test credentials")
