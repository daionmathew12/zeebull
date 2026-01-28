import requests
import json

# First, login to get a token
login_url = "https://teqmates.com/orchidapi/api/auth/login"
login_payload = {
    "email": "basil@gmail.com",
    "password": "admin123"
}

print("Logging in...")
login_response = requests.post(login_url, json=login_payload)
print(f"Login Status: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json().get("access_token")
    print(f"Got token: {token[:20]}...")
    
    # Now try clock-in
    clockin_url = "https://teqmates.com/orchidapi/api/attendance/clock-in"
    clockin_payload = {
        "employee_id": 31,
        "location": "Test Location"
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\nAttempting clock-in...")
    clockin_response = requests.post(clockin_url, json=clockin_payload, headers=headers)
    print(f"Clock-in Status: {clockin_response.status_code}")
    print(f"Response: {clockin_response.text}")
else:
    print(f"Login failed: {login_response.text}")
