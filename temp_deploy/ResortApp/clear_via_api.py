"""Clear all services via API endpoint"""
import requests
import json

# First, login to get token
login_url = "http://localhost:8011/api/auth/login"
login_data = {
    "email": "admin@example.com",
    "password": "admin123"
}

print("Logging in...")
try:
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code == 200:
        token = login_response.json().get("access_token")
        print("✓ Login successful")
    else:
        print(f"✗ Login failed: {login_response.status_code}")
        print(login_response.text)
        exit(1)
except Exception as e:
    print(f"✗ Login error: {e}")
    exit(1)

# Now call the clear endpoint
clear_url = "http://localhost:8011/api/services/clear-all"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("\nClearing all services...")
try:
    response = requests.delete(clear_url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print("✓ Success!")
        print(json.dumps(result, indent=2))
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"✗ Error: {e}")



