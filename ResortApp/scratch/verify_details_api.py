
import requests
import json

def test_booking_details():
    base_url = "http://127.0.0.1:8011/api"
    
    # 1. Login
    print("Logging in...")
    login_data = {"username": "admin", "password": "password"} # Assuming default creds
    try:
        response = requests.post(f"{base_url}/auth/login", data=login_data)
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get booking 6 details
        print("Fetching booking 6 details...")
        # Note: Booking number BK-2-000006. We need the ID.
        # From previous script, Booking ID is 6.
        resp = requests.get(f"{base_url}/bookings/6/details", headers=headers)
        if resp.status_code != 200:
            print(f"Fetch failed: {resp.text}")
            return
            
        details = resp.json()
        print("\nBooking Details Response (inventory_usage):")
        print(json.dumps(details.get("inventory_usage", []), indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_booking_details()
