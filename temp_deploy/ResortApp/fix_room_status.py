"""
Script to update rooms 100, 101, 102 status to Available
"""
import requests

BASE_URL = "http://localhost:8011/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
ROOMS_URL = f"{BASE_URL}/rooms"

CREDS = {
    "email": "admin@orchid.com",
    "password": "admin123"
}

def update_room_status():
    print("=" * 80)
    print("UPDATING ROOMS 100, 101, 102 TO AVAILABLE STATUS")
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
    
    # Get all rooms to find IDs
    print("\n2. Fetching rooms to get IDs...")
    try:
        resp = requests.get(f"{ROOMS_URL}/?limit=100", headers=headers)
        if resp.status_code != 200:
            print(f"Failed to fetch rooms: {resp.status_code}")
            return
        
        rooms = resp.json()
        target_rooms = {}
        
        for room in rooms:
            if room['number'] in ['100', '101', '102']:
                target_rooms[room['number']] = room
        
        print(f"   Found {len(target_rooms)} rooms to update")
        
        # Update each room
        print("\n3. Updating room statuses...")
        for room_num, room in target_rooms.items():
            room_id = room['id']
            current_status = room.get('status', 'Unknown')
            
            print(f"\n   Room {room_num} (ID: {room_id}):")
            print(f"     Current status: {current_status}")
            
            # Update to Available
            form_data = {
                "status": "Available"
            }
            
            try:
                update_resp = requests.put(
                    f"{ROOMS_URL}/{room_id}",
                    data=form_data,
                    headers=headers
                )
                
                if update_resp.status_code == 200:
                    print(f"     ✓ Updated to: Available")
                else:
                    print(f"     ❌ Update failed: {update_resp.status_code} - {update_resp.text[:200]}")
            except Exception as e:
                print(f"     ❌ Error: {e}")
        
        # Verify updates
        print("\n4. Verifying updates...")
        resp = requests.get(f"{ROOMS_URL}/?limit=100", headers=headers)
        if resp.status_code == 200:
            rooms = resp.json()
            for room in rooms:
                if room['number'] in ['100', '101', '102']:
                    print(f"   Room {room['number']}: {room.get('status')}")
        
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("DONE! Please refresh the booking page to see the rooms.")
    print("=" * 80)

if __name__ == "__main__":
    update_room_status()
