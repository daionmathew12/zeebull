
import requests
import datetime

BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
CLOCK_IN_URL = f"{BASE_URL}/attendance/clock-in"

EMAIL = "server2@orchid.com"
PASSWORD = "password123"

def clock_in():
    print(f"Logging in as {EMAIL}...")
    try:
        # Login
        resp = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} - {resp.text}")
            return
        
        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Clock In
        print("Clocking in...")
        # Clock in endpoint usually takes coordinates or is simple POST
        data = {
            "employee_id": 9,
            "location": "Front Desk",
            "latitude": 0.0,
            "longitude": 0.0,
            "address": "Front Desk"
        }
        
        # Check if clock-in requires query params or body 
        # Typically body.
        
        resp = requests.post(CLOCK_IN_URL, json=data, headers=headers)
        if resp.status_code == 200:
            print("Clocked in successfully!")
            print(resp.json())
        else:
            print(f"Clock-in failed: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clock_in()
