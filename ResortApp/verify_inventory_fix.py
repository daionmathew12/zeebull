
import requests
import json

# The server is reported on port 8012 in user metadata
BASE_URL = "http://localhost:8012/api"

def verify_endpoints():
    endpoints = [
        "/inventory/items?limit=5",
        "/inventory/categories?limit=5",
        "/inventory/waste-logs?limit=5"
    ]
    
    print(f"--- Verifying Inventory Fixes on {BASE_URL} ---")
    
    all_passed = True
    for ep in endpoints:
        url = BASE_URL + ep
        print(f"Testing {url}...", end=" ")
        try:
            # We don't have a token here, but some GET endpoints might be public 
            # or the server might be running without strict auth in dev?
            # Actually, the user logs showed 500s AFTER the OPTIONS call, 
            # so we can at least check if 500 is gone.
            response = requests.get(url, timeout=10)
            if response.status_code == 500:
                print(f"FAILED (Status 500)")
                print(f"Error Detail: {response.text[:200]}")
                all_passed = False
            elif response.status_code == 401:
                print(f"REACHABLE (Status 401 Unauthorized - Expected if token required)")
            else:
                print(f"SUCCESS (Status {response.status_code})")
        except Exception as e:
            print(f"CONNECTION ERROR: {e}")
            all_passed = False
            
    return all_passed

if __name__ == "__main__":
    verify_endpoints()
