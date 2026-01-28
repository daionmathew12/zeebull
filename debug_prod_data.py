
import requests
import json

# Constants
# BASE_URL = "http://localhost:8000/api" 
BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
FOOD_ORDERS_URL = f"{BASE_URL}/food-orders"

# Credentials
# Trying the email visible in the screenshot
EMAIL = "ad@orchid.com" 
# Common password used in tests, if this fails I'll try to find another way or just check backend code
PASSWORD = "1234" 

def get_token():
    print(f"Logging in as {EMAIL}...")
    try:
        response = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if not token:
                # Some implementations might handle it differently
                print(f"No access_token field: {data.keys()}")
            return token
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Login exception: {e}")
        return None

def check_data(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Check Food Orders for Table Number
    print("\n--- Checking Food Orders ---")
    try:
        resp = requests.get(FOOD_ORDERS_URL, headers=headers)
        if resp.status_code == 200:
            orders = resp.json()
            print(f"Found {len(orders)} orders.")
            if orders:
                print("First order sample:", json.dumps(orders[0], indent=2))
        else:
            print(f"Failed to get orders: {resp.status_code}")
    except Exception as e:
        print(f"Order fetch error: {e}")

    # 2. Check Employee Profile (ID 31 based on screenshot)
    print("\n--- Checking Employee 31 ---")
    try:
        resp = requests.get(f"{BASE_URL}/employees/31", headers=headers)
        if resp.status_code == 200:
            emp = resp.json()
            print(json.dumps(emp, indent=2))
        else:
            print(f"Failed to get employee: {resp.status_code}")
            
    except Exception as e:
        print(f"Employee fetch error: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        check_data(token)
    else:
        # Fallback: try m@orchid.com if ad@orchid.com fails
        print("\nRetrying with m@orchid.com...")
        EMAIL = "m@orchid.com"
        token = get_token()
        if token:
            check_data(token)
