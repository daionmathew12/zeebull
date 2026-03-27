"""
Script to create missing rooms 100, 101, 102 in the database
"""
import requests

BASE_URL = "http://localhost:8011/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
ROOMS_URL = f"{BASE_URL}/rooms/"

CREDS = {
    "email": "admin@orchid.com",
    "password": "admin123"
}

def create_missing_rooms():
    print("=" * 80)
    print("CREATING MISSING ROOMS 100, 101, 102")
    print("=" * 80)
    
    # Login
    print("\n1. Logging in...")
    try:
        resp = requests.post(LOGIN_URL, json=CREDS)
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} - {resp.text}")
            return
        token = resp.json().get("access_token")
        print(f"✓ Login successful")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Define the missing rooms
    missing_rooms = [
        {
            "number": "100",
            "type": "Standard Room",
            "price": 3000.0,
            "status": "Available",
            "adults": 2,
            "children": 0
        },
        {
            "number": "101",
            "type": "Standard Room",
            "price": 3000.0,
            "status": "Available",
            "adults": 2,
            "children": 0
        },
        {
            "number": "102",
            "type": "Standard Room",
            "price": 3000.0,
            "status": "Available",
            "adults": 2,
            "children": 0
        }
    ]
    
    print("\n2. Creating missing rooms...")
    for room_data in missing_rooms:
        try:
            # Use form data instead of JSON
            form_data = {
                "number": room_data["number"],
                "type": room_data["type"],
                "price": str(room_data["price"]),
                "status": room_data["status"],
                "adults": str(room_data["adults"]),
                "children": str(room_data["children"]),
                "air_conditioning": "false",
                "wifi": "false",
                "bathroom": "false",
                "living_area": "false",
                "terrace": "false",
                "parking": "false",
                "kitchen": "false",
                "family_room": "false",
                "bbq": "false",
                "garden": "false",
                "dining": "false",
                "breakfast": "false"
            }
            
            resp = requests.post(ROOMS_URL, data=form_data, headers=headers)
            if resp.status_code == 200:
                print(f"   ✓ Room {room_data['number']} created successfully")
            else:
                print(f"   ❌ Failed to create room {room_data['number']}: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"   ❌ Error creating room {room_data['number']}: {e}")
    
    # Verify the rooms were created
    print("\n3. Verifying rooms were created...")
    try:
        resp = requests.get(f"{ROOMS_URL}?limit=100", headers=headers)
        if resp.status_code == 200:
            rooms = resp.json()
            room_numbers = [r['number'] for r in rooms]
            print(f"   Total rooms: {len(rooms)}")
            print(f"   Room numbers: {sorted(room_numbers)}")
            
            for num in ['100', '101', '102']:
                if num in room_numbers:
                    print(f"   ✓ Room {num} exists")
                else:
                    print(f"   ❌ Room {num} still missing")
        else:
            print(f"   Failed to fetch rooms: {resp.status_code}")
    except Exception as e:
        print(f"   Error verifying rooms: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    create_missing_rooms()
