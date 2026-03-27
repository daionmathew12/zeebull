import requests
import time
import os

BASE_URL = "http://localhost:8011/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
CHECKOUT_INV_URL = f"{BASE_URL}/bill/checkout-request/2/inventory-details"

CREDS = {
    "email": "admin@orchid.com",
    "password": "admin123"
}

def run_test():
    print(f"Logging in to {LOGIN_URL}...")
    try:
        resp = requests.post(LOGIN_URL, json=CREDS)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return
    
    token = resp.json().get("access_token")
    print(f"Got Token: {token[:10]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Requesting Inventory Details: {CHECKOUT_INV_URL}...")
    inv_resp = requests.get(CHECKOUT_INV_URL, headers=headers)
    
    print(f"Response Code: {inv_resp.status_code}")
    try:
        data = inv_resp.json()
        print(f"Response Body Keys: {data.keys()}")
        items = data.get("items", [])
        print(f"Items Count: {len(items)}")
        if items:
            for i in items:
                print(f" - {i.get('item_name')}: {i.get('current_stock')}")
        else:
            print("ITEMS ARRAY IS EMPTY")
    except:
        print(f"Response Text: {inv_resp.text}")

    # Read debug log
    # Skipped log dump
    print("\nTest Complete")

if __name__ == "__main__":
    run_test()
