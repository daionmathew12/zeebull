"""Test login endpoint"""
import requests
import json

url = "http://localhost:8000/api/auth/login"
data = {"email": "m@orchid.com", "password": "1234"}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
