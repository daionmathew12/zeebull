import requests

login_data = {
    "email": "housekeeping1@example.com",
    "password": "password123"
}
response = requests.post("http://34.30.59.169/api/auth/login", json=login_data)
if response.status_code == 200:
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://34.30.59.169/api/auth/me", headers=headers)
    print(response.json())
else:
    print("Login failed:", response.text)
