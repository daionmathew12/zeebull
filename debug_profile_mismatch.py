
import requests
import json

# Constants
BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
PROFILE_URL = f"{BASE_URL}/auth/me"
EMPLOYEE_URL = f"{BASE_URL}/employees/31"

# Credentials
EMAIL = "ad@orchid.com" 
PASSWORD = "1234" 

def get_token():
    print(f"Logging in as {EMAIL}...")
    try:
        response = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def check_profiles(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Check /auth/me
    print("\n--- Checking /auth/me ---")
    try:
        resp = requests.get(PROFILE_URL, headers=headers)
        if resp.status_code == 200:
            me = resp.json()
            print(json.dumps(me, indent=2))
        else:
            print(f"Failed to get /auth/me: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Check /employees/31
    print("\n--- Checking /employees/31 ---")
    try:
        resp = requests.get(EMPLOYEE_URL, headers=headers)
        if resp.status_code == 200:
            emp = resp.json()
            print(json.dumps(emp, indent=2))
        else:
            print(f"Failed to get employee: {resp.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        check_profiles(token)
    else: 
        # try m@orchid.com
        print("Trying m@orchid.com")
        EMAIL = "m@orchid.com"
        token = get_token()
        if token: check_profiles(token)
