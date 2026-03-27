import requests
import json
import time

def trigger_active_rooms():
    url = "http://localhost:8011/api/bill/active-rooms"
    print(f"Calling Active Rooms Endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response Size: ", len(response.text))
            try:
                data = response.json()
                print(f"Active Rooms Count: {len(data)}")
                for room in data:
                    print(f"  - Room {room.get('room_number')} (Booking ID: {room.get('booking_id')}) (Status: {room.get('booking_status')})")
            except Exception as e:
                print("Failed to parse JSON response")
        else:
            print(f"Failed to call endpoint: {response.text}")
    except requests.exceptions.ConnectionError:
        print("Connection failed! Is the server running?")
        # Try finding port by check_all_processes? No I know it.
        # Maybe port 8000? 8011? 8012?
        for port in [8000, 8011, 8012]:
            url = f"http://localhost:{port}/api/bill/active-rooms"
            print(f"Trying port {port}...")
            try:
                requests.get(url, timeout=2)
                print(f"Connected on port {port}!")
                break
            except:
                pass
                
if __name__ == "__main__":
    trigger_active_rooms()
