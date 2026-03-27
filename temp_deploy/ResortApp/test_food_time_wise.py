import requests
import json

BASE_URL = "http://localhost:8011/api"

def test_food_item_creation():
    # Login as admin
    login_data = {"email": "admin@orchid.com", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print("Login Failed:", response.text)
        return
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Get categories to get a valid category_id
    response = requests.get(f"{BASE_URL}/food-categories", headers=headers)
    categories = response.json()
    if not isinstance(categories, list):
        print("Categories response is not a list:", categories)
        return
    if not categories:
        print("No categories found, cannot test.")
        return
    category_id = categories[0]["id"]

    # Test data
    time_wise_prices = [
        {"from_time": "08:00", "to_time": "11:00", "price": 100},
        {"from_time": "12:00", "to_time": "15:00", "price": 150}
    ]
    
    data = {
        "name": "Test Time-wise Food",
        "description": "A food item with time-dependent pricing",
        "price": 200,
        "available": "true",
        "category_id": category_id,
        "always_available": "false",
        "available_from_time": "08:00",
        "available_to_time": "22:00",
        "time_wise_prices": json.dumps(time_wise_prices),
        "room_service_price": 220
    }

    # Create item
    response = requests.post(f"{BASE_URL}/food-items", data=data, headers=headers)
    print("Creation Response:", response.status_code)
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        item_id = response.json()["id"]
        # Verify it has the fields
        response = requests.get(f"{BASE_URL}/food-items", headers=headers)
        items = response.json()
        item = next((i for i in items if i["id"] == item_id), None)
        if item:
            print("\nVerified Item Data:")
            print(f"Name: {item['name']}")
            print(f"Time-wise Prices: {item['time_wise_prices']}")
            print(f"Room Service Price: {item['room_service_price']}")
            print(f"Always Available: {item['always_available']}")
        else:
            print("Item not found in list!")

if __name__ == "__main__":
    test_food_item_creation()
