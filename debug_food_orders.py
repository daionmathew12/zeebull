
import requests
import json
import sys

# Constants
BASE_URL = "http://localhost:8000/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
FOOD_ORDERS_URL = f"{BASE_URL}/food-orders"

# Credentials (using what was in test_login.py)
EMAIL = "m@orchid.com"
PASSWORD = "1234"

def get_token():
    print(f"Logging in as {EMAIL}...")
    try:
        response = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
        if response.status_code == 200:
            token = response.json().get("access_token") 
            # Check if token is directly returned or in a specific field
            if not token and "token" in response.json():
                 token = response.json()["token"]
            
            if token:
                print("Login successful.")
                return token
            else:
                print(f"Login successful but no token found in response: {response.text}")
                return None
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login exception: {e}")
        return None

def fetch_food_orders(token):
    print("Fetching food orders...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(FOOD_ORDERS_URL, headers=headers)
        if response.status_code == 200:
            orders = response.json()
            print(f"Fetched {len(orders)} orders.")
            print(json.dumps(orders, indent=2))
        else:
            print(f"Fetch failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Fetch exception: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        fetch_food_orders(token)
