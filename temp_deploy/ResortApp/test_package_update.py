"""
Test package update directly via API
"""
import requests
import json

# Get auth token first
login_url = "http://localhost:8011/api/login"
login_data = {
    "username": "admin",  # Change if needed
    "password": "admin123"  # Change if needed
}

print("=" * 60)
print("TESTING PACKAGE UPDATE")
print("=" * 60)

try:
    # Login to get token
    print("\n1. Logging in...")
    login_response = requests.post(login_url, data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        exit(1)
    
    token = login_response.json().get("access_token")
    print(f"✓ Login successful! Token: {token[:20]}...")
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Update package (ID 1 - honeymoon)
    print("\n2. Updating package...")
    update_url = "http://localhost:8011/api/packages/1"
    
    # Prepare form data
    update_data = {
        "title": "honeymoon",
        "description": "Updated description - TEST",
        "price": "15000",  # Changed from 10000 to 15000
        "booking_type": "room_type",
        "room_types": "Deluxe,luxury"
    }
    
    update_response = requests.put(update_url, data=update_data, headers=headers)
    
    if update_response.status_code == 200:
        print(f"✓ Package updated successfully!")
        result = update_response.json()
        print(f"\nUpdated package:")
        print(f"  Title: {result.get('title')}")
        print(f"  Description: {result.get('description')}")
        print(f"  Price: {result.get('price')}")
    else:
        print(f"❌ Update failed: {update_response.status_code}")
        print(f"Response: {update_response.text}")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
