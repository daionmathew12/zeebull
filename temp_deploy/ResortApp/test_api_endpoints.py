"""Test API endpoints to identify which one is failing"""
import requests
import sys

BASE_URL = "http://localhost:8011/api"

# Test endpoints that the Bookings page calls
endpoints = [
    "/rooms/",
    "/bookings?skip=0&limit=20&order_by=id&order=desc",
    "/packages/bookingsall?skip=0&limit=500",
    "/packages/",
    "/inventory/items?limit=500",
    "/inventory/locations?limit=10000",
]

print("Testing API endpoints...")
print("=" * 60)

# You'll need to add a valid token here if authentication is required
# For now, testing without auth to see which endpoints are accessible
headers = {}

failed_endpoints = []
for endpoint in endpoints:
    url = BASE_URL + endpoint
    try:
        print(f"\nTesting: {endpoint}")
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"  ✓ SUCCESS (200 OK)")
        else:
            print(f"  ✗ FAILED ({response.status_code})")
            print(f"    Response: {response.text[:200]}")
            failed_endpoints.append((endpoint, response.status_code, response.text[:200]))
    except Exception as e:
        print(f"  ✗ ERROR: {str(e)}")
        failed_endpoints.append((endpoint, "ERROR", str(e)))

print("\n" + "=" * 60)
print("\nSUMMARY:")
if failed_endpoints:
    print(f"\n{len(failed_endpoints)} endpoint(s) failed:")
    for endpoint, status, msg in failed_endpoints:
        print(f"  - {endpoint}: {status}")
        print(f"    {msg[:100]}")
else:
    print("\n✓ All endpoints working!")
