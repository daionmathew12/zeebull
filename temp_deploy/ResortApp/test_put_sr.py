import requests

url = "http://localhost:8000/api/service-requests/10"
payload = {"status": "completed"}
headers = {"Content-Type": "application/json"} # no auth for testing local if auth is disabled?
try:
    response = requests.put(url, json=payload, headers=headers)
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
except Exception as e:
    print("Error:", e)
