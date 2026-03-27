import requests
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NzM3NzUzODd9.1YL9YiOMGbMb40mMSCxkc5ZNsZyMUAHuuoaGiMeRfH0"
headers = {"Authorization": f"Bearer {token}"}

url = "http://localhost:8011/api/services/assigned?skip=0&limit=50"
print(f"Calling {url}...")
try:
    r = requests.get(url, headers=headers)
    print(f"Status Code: {r.status_code}")
    print("Response:")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Request failed: {e}")
