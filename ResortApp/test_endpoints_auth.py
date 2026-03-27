import requests
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NzM3NzUzODd9.1YL9YiOMGbMb40mMSCxkc5ZNsZyMUAHuuoaGiMeRfH0"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "X-Branch-ID": "all"
}
BASE_URL = "http://localhost:8011/api"

def test_endpoint(endpoint):
    print(f"\n--- Testing {endpoint} ---")
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text}")
        else:
            data = response.json()
            print(f"Success: Found {len(data) if isinstance(data, list) else '1'} items")
    except Exception as e:
        print(f"Error: {e}")

test_endpoint("/service-requests?limit=50")
test_endpoint("/services/assigned?limit=50")
