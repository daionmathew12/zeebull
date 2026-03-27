import requests
import sys

def test_login(email, password):
    url = "http://localhost:8011/api/auth/login"
    payload = {
        "email": email,
        "password": password
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login("a@h.com", "1234")
