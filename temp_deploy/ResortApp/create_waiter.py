
import requests

BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
EMPLOYEES_URL = f"{BASE_URL}/employees"

EMAIL = "m@orchid.com"
PASSWORD = "1234"

def get_token():
    try:
        response = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def create_waiter(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "John Waiter",
        "role": "Waiter",
        "salary": 15000,
        "join_date": "2026-01-27",
        "email": "server2@orchid.com",
        "password": "password123",
        "phone": "9876543210"
    }
    
    print("\n--- Creating Waiter ---")
    try:
        resp = requests.post(EMPLOYEES_URL, headers=headers, data=data) 
        # Note: Using data=data for Form fields if the API expects Form, 
        # but requests usually handles dict as form-encoded if files not present? 
        # Wait, the API uses Form(...). requests.post(data=...) sends form-encoded.
        
        if resp.status_code == 200 or resp.status_code == 201:
            print("Waiter created successfully!")
            print(resp.json())
        else:
            print(f"Failed to create waiter: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    token = get_token()
    if token:
        create_waiter(token)
