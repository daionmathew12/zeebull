
import requests
import json

BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
EMPLOYEES_URL = f"{BASE_URL}/employees"

EMAIL = "m@orchid.com"
PASSWORD = "1234"

def get_token():
    try:
        response = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_employees_endpoint(token):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n--- Testing /employees/ endpoint ---")
    try:
        # Test without trailing slash
        resp1 = requests.get(f"{BASE_URL}/employees", headers=headers)
        print(f"GET /employees - Status: {resp1.status_code}")
        if resp1.status_code == 200:
            data1 = resp1.json()
            print(f"Returned {len(data1)} employees")
            if len(data1) > 0:
                print(f"First employee: {json.dumps(data1[0], indent=2)}")
        else:
            print(f"Error: {resp1.text}")
        
        # Test with trailing slash
        print(f"\n--- Testing /employees/ endpoint (with slash) ---")
        resp2 = requests.get(f"{BASE_URL}/employees/", headers=headers)
        print(f"GET /employees/ - Status: {resp2.status_code}")
        if resp2.status_code == 200:
            data2 = resp2.json()
            print(f"Returned {len(data2)} employees")
            if len(data2) > 0:
                print(f"First employee: {json.dumps(data2[0], indent=2)}")
        else:
            print(f"Error: {resp2.text}")
            
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        print(f"Token obtained: {token[:20]}...")
        test_employees_endpoint(token)
