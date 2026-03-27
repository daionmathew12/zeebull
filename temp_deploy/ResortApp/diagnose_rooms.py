"""
Script to check if rooms 100, 101, 102 have conflicting bookings
"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8011/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
ROOMS_URL = f"{BASE_URL}/rooms/"
BOOKINGS_URL = f"{BASE_URL}/bookings"

CREDS = {
    "email": "admin@orchid.com",
    "password": "admin123"
}

def check_room_conflicts():
    print("=" * 80)
    print("CHECKING ROOM CONFLICTS FOR 100, 101, 102")
    print("=" * 80)
    
    # Login
    print("\n1. Logging in...")
    try:
        resp = requests.post(LOGIN_URL, json=CREDS)
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code}")
            return
        token = resp.json().get("access_token")
        print(f"✓ Login successful")
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get rooms
    print("\n2. Fetching rooms 100, 101, 102...")
    try:
        resp = requests.get(f"{ROOMS_URL}?limit=100", headers=headers)
        if resp.status_code != 200:
            print(f"Failed: {resp.status_code}")
            return
        
        rooms = resp.json()
        target_rooms = {r['number']: r for r in rooms if r['number'] in ['100', '101', '102']}
        
        print(f"   Found {len(target_rooms)} rooms:")
        for num, room in target_rooms.items():
            print(f"     Room {num}: ID={room['id']}, Type={room.get('type')}, Status={room.get('status')}")
        
        if len(target_rooms) == 0:
            print("   ❌ ROOMS DO NOT EXIST IN DATABASE!")
            return
            
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Get all bookings
    print("\n3. Fetching all bookings...")
    try:
        resp = requests.get(f"{BOOKINGS_URL}?limit=500&order_by=id&order=desc", headers=headers)
        if resp.status_code != 200:
            print(f"Failed: {resp.status_code}")
            return
        
        bookings_data = resp.json()
        bookings = bookings_data.get('bookings', [])
        print(f"   Total bookings: {len(bookings)}")
        
        # Check for conflicts
        print("\n4. Checking for booking conflicts:")
        for room_num in ['100', '101', '102']:
            print(f"\n   Room {room_num}:")
            conflicts = []
            
            for booking in bookings:
                # Skip cancelled bookings
                if booking.get('status', '').lower() == 'cancelled':
                    continue
                
                # Check if this booking includes the room
                booking_rooms = booking.get('rooms', [])
                room_in_booking = False
                
                for br in booking_rooms:
                    br_num = br.get('number') or br.get('room', {}).get('number')
                    if br_num == room_num:
                        room_in_booking = True
                        break
                
                if room_in_booking:
                    conflicts.append({
                        'id': booking.get('id'),
                        'status': booking.get('status'),
                        'check_in': booking.get('check_in'),
                        'check_out': booking.get('check_out'),
                        'guest': booking.get('guest_name')
                    })
            
            if conflicts:
                print(f"     Found {len(conflicts)} booking(s):")
                for c in conflicts:
                    print(f"       - Booking {c['id']}: {c['status']}, {c['check_in']} to {c['check_out']}, Guest: {c['guest']}")
            else:
                print(f"     ✓ No bookings found")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_room_conflicts()
