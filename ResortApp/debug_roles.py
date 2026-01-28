
import requests
import json

BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
ROLES_URL = f"{BASE_URL}/roles"

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

def check_roles(token):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n--- Checking Roles ({ROLES_URL}) ---")
    try:
        resp = requests.get(ROLES_URL, headers=headers)
        if resp.status_code == 200:
            roles = resp.json()
            print(f"Found {len(roles)} roles.")
            for r in roles:
                print(f"ID: {r['id']}, Name: {r['name']}")
        else:
            print(f"Failed to get roles: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        check_roles(token)
