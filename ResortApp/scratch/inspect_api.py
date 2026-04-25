import requests
import json

base_url = "http://localhost:8011"
booking_id = 7 # BK-000007

try:
    resp = requests.get(f"{base_url}/api/bookings/details/{booking_id}")
    if resp.status_code == 200:
        data = resp.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"Connection Error: {e}")
