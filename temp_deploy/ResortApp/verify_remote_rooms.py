import requests
import time

def check_remote_active():
    url = "http://34.30.59.169:8011/api/bill/active-rooms"
    print(f"Checking remote endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Active Rooms: {len(data)}")
            
            found_103 = False
            for item in data:
                r_num = item.get('room_number')
                status = item.get('booking_status', 'N/A')
                b_id = item.get('booking_id')
                
                if r_num == '103':
                    found_103 = True
                    print(f"!!! FOUND ROOM 103 !!! Booking ID: {b_id}, Status: {status}")
                else:
                    # print(f"  Room {r_num} (ID: {b_id})")
                    pass
            
            if not found_103:
                print("Room 103 NOT found in active rooms list.")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    check_remote_active()
