import requests

url = "http://localhost:8011/api/attendance/status/today"
params = {"branch_id": 2}
headers = {"X-Branch-ID": "2"} # Add header too just in case

try:
    # First try with login if needed, but maybe public?
    # Actually, I'll just check if I can get a token
    # For now, let's assume I can call it if it's the same machine
    response = requests.get(url, params=params, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
