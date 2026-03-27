import requests

base_url = "http://localhost:8011/api"

endpoints = [
    "/inventory/items",
    "/inventory/categories",
    "/inventory/vendors",
    "/inventory/purchases",
    "/inventory/asset-mappings"
]

for ep in endpoints:
    try:
        url = base_url + ep
        print(f"Testing {url}...")
        res = requests.get(url)
        print(f"Status: {res.status_code}")
        if res.status_code != 200:
            print(f"Response: {res.text[:200]}")
    except Exception as e:
        print(f"Error accessing {ep}: {e}")
