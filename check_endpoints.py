
import requests

BASE_URL = "http://localhost:8011/api"

# We need a token. I'll try to find one or just check if the endpoints exist and return something.
# Since I can't easily get a token without credentials, I'll check if the server responds at least with 401/403 or some other error.

endpoints = [
    "/employees",
    "/attendance/utilization/aggregate",
    "/attendance/holidays",
    "/attendance/status/today"
]

for ep in endpoints:
    try:
        url = BASE_URL + ep
        print(f"Checking {url}...")
        resp = requests.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Error checking {ep}: {e}")
