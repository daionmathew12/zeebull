
import requests
import json

url = "https://teqmates.com/orchidapi/api/attendance/clock-in"
payload = {
    "employee_id": 31,
    "location": "Debug Script"
}
headers = {
    "Content-Type": "application/json"
}

print(f"Testing POST to {url}...")
try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
