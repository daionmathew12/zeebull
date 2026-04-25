
import requests
import json

def check_api():
    base_url = "http://127.0.0.1:8011/api"
    
    # Login
    login_data = {"username": "admin", "password": "password"}
    resp = requests.post(f"{base_url}/auth/login", data=login_data)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get orders
    resp = requests.get(f"{base_url}/food-orders/", headers=headers)
    orders = resp.json()
    
    print("Recent Food Orders:")
    for o in orders[:5]:
        print(f"Order #{o['id']} (Type: {o['order_type']}, Total: {o['total_with_gst']})")
        for i in o['items']:
            print(f"  - {i['food_item_name']}: Price: {i.get('price')}, Subtotal: {i.get('subtotal')}")

if __name__ == "__main__":
    check_api()
