
import requests
import json

BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"

EMAIL = "m@orchid.com"
PASSWORD = "1234"

def test_food_orders_page():
    # Step 1: Login
    print("=== Step 1: Login ===")
    login_response = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json().get("access_token")
    print(f"[OK] Login successful, token: {token[:20]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Test /employees endpoint (without slash)
    print("\n=== Step 2: Test /employees (no slash) ===")
    emp_response = requests.get(f"{BASE_URL}/employees", headers=headers)
    print(f"Status: {emp_response.status_code}")
    if emp_response.status_code == 200:
        employees = emp_response.json()
        print(f"[OK] Returned {len(employees)} employees")
        for emp in employees[:3]:  # Show first 3
            print(f"  - {emp['name']} (ID: {emp['id']}, Status: {emp.get('status', 'N/A')})")
    else:
        print(f"[ERROR] {emp_response.text}")
    
    # Step 3: Test /employees/ endpoint (with slash)
    print("\n=== Step 3: Test /employees/ (with slash) ===")
    emp_slash_response = requests.get(f"{BASE_URL}/employees/", headers=headers)
    print(f"Status: {emp_slash_response.status_code}")
    if emp_slash_response.status_code == 200:
        employees_slash = emp_slash_response.json()
        print(f"[OK] Returned {len(employees_slash)} employees")
    else:
        print(f"[ERROR] {emp_slash_response.text}")
    
    # Step 4: Test /food-items/ endpoint
    print("\n=== Step 4: Test /food-items/ (with slash) ===")
    food_response = requests.get(f"{BASE_URL}/food-items/", headers=headers)
    print(f"Status: {food_response.status_code}")
    if food_response.status_code == 200:
        food_items = food_response.json()
        print(f"[OK] Returned {len(food_items)} food items")
    else:
        print(f"[ERROR] {food_response.text}")
    
    # Step 5: Test /food-items endpoint (without slash)
    print("\n=== Step 5: Test /food-items (no slash) ===")
    food_no_slash_response = requests.get(f"{BASE_URL}/food-items", headers=headers)
    print(f"Status: {food_no_slash_response.status_code}")
    if food_no_slash_response.status_code == 200:
        food_items_no_slash = food_no_slash_response.json()
        print(f"[OK] Returned {len(food_items_no_slash)} food items")
    else:
        print(f"[ERROR] {food_no_slash_response.text}")
    
    print("\n=== Summary ===")
    print(f"/employees (no slash): {emp_response.status_code}")
    print(f"/employees/ (with slash): {emp_slash_response.status_code}")
    print(f"/food-items/ (with slash): {food_response.status_code}")
    print(f"/food-items (no slash): {food_no_slash_response.status_code}")

if __name__ == "__main__":
    test_food_orders_page()
