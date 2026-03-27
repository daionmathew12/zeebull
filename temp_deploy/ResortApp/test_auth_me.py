"""Test /auth/me endpoint"""
import requests
import json

# First login to get a token
login_url = "http://localhost:8000/api/auth/login"
login_data = {"email": "m@orchid.com", "password": "1234"}

try:
    login_response = requests.post(login_url, json=login_data)
    print(f"Login Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        print(f"Token received: {token[:50]}...")
        
        # Now test /auth/me
        me_url = "http://localhost:8000/api/auth/me"
        headers = {"Authorization": f"Bearer {token}"}
        
        me_response = requests.get(me_url, headers=headers)
        print(f"\n/auth/me Status: {me_response.status_code}")
        print(f"/auth/me Response: {json.dumps(me_response.json(), indent=2)}")
    else:
        print(f"Login failed: {login_response.text}")
        
except Exception as e:
    print(f"Error: {e}")
