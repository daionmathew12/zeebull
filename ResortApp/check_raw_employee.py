
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
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def check_raw(token):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n--- Checking Raw Employee Data ---")
    try:
        params = {"limit": 100}
        resp = requests.get(EMPLOYEES_URL, headers=headers, params=params)
        if resp.status_code == 200:
            employees = resp.json()
            # Find John Waiter
            john = next((e for e in employees if "John Waiter" in e["name"]), None)
            if john:
                print("John Waiter Raw Data:")
                print(json.dumps(john, indent=2))
            else:
                print("John Waiter not found. Printing first employee:")
                print(json.dumps(employees[0], indent=2))
        else:
            print(f"Failed to get employees: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"Prod API Error: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        check_raw(token)
