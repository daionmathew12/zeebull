
import requests
import json

BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
ITEMS_URL = f"{BASE_URL}/inventory/items"

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

def check_items(token):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n--- Checking Prod Inventory Items ---")
    try:
        params = {"limit": 100}
        resp = requests.get(ITEMS_URL, headers=headers, params=params)
        if resp.status_code == 200:
            items = resp.json()
            # print IDs for Smart TV and LED Bulb
            targets = ["Smart TV", "LED Bulb", "Tv", "Mineral water", "coca cola"]
            found = []
            for item in items:
                if item["name"] in targets:
                    print(f"Server Item: {item['name']} (ID: {item['id']})")
                    found.append(item["name"])
                
                # Also check raw ID 3 and 4
                if item["id"] in [3, 4]:
                     print(f"Server Item ID {item['id']}: {item['name']}")

        else:
            print(f"Failed to get items: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"Prod API Error: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        check_items(token)
