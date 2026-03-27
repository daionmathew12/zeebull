"""
Test the services API endpoint directly
"""
import requests
import json

base_url = "http://localhost:8011"

# First, let's try without authentication to see the error
print("=" * 60)
print("TESTING SERVICES API ENDPOINT")
print("=" * 60)

try:
    print("\n1. Testing GET /api/services (without auth)...")
    response = requests.get(f"{base_url}/api/services?limit=100")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 401:
        print("   ✓ API requires authentication (expected)")
        print(f"   Response: {response.text[:200]}")
    elif response.status_code == 200:
        data = response.json()
        print(f"   ✓ API returned {len(data)} services")
        if data:
            print(f"\n   First service:")
            print(f"   {json.dumps(data[0], indent=2)}")
    else:
        print(f"   ✗ Unexpected status code: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNOTE: If the API requires authentication, you need to:")
print("1. Open the browser console (F12)")
print("2. Check the Network tab for the /api/services request")
print("3. Look for any error messages")
print("4. Verify the Authorization header is being sent")
