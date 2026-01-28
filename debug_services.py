
import requests
import json
import os

BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
SERVICES_URL = f"{BASE_URL}/services"

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

def check_services(token):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n--- Fetching Services from {SERVICES_URL} ---")
    try:
        resp = requests.get(SERVICES_URL, headers=headers)
        if resp.status_code == 200:
            services = resp.json()
            if isinstance(services, list) and len(services) > 0:
                print(f"Found {len(services)} services. Inspecting first one:")
                print(json.dumps(services[0], indent=2))
                
                # Check for one with 'oil' in name if possible
                for s in services:
                    if 'massage' in s.get('name', '').lower() or 'oil' in str(s).lower():
                        print("\n--- Found Potential Match ---")
                        print(json.dumps(s, indent=2))
                        break
            else:
                print("No services found or empty list.")
                print(services)
        else:
            print(f"Failed to get services: {resp.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        check_services(token)
