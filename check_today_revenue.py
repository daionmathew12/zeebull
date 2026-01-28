import requests

# Login
login_url = "https://teqmates.com/orchidapi/api/auth/login"
login_payload = {"email": "admin@orchid.com", "password": "admin123"}

response = requests.post(login_url, json=login_payload)
if response.status_code == 200:
    token = response.json().get("access_token")
    
    # Get today's dashboard summary
    dashboard_url = "https://teqmates.com/orchidapi/api/dashboard/summary"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(dashboard_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("=== BACKEND DASHBOARD DATA ===")
        print(f"Today's Revenue: ₹{data.get('revenue', 0)}")
        print(f"Today's Expenses: ₹{data.get('expenses', 0)}")
        print(f"Net Profit: ₹{data.get('net_profit', 0)}")
        print(f"\nFull response: {data}")
    else:
        print(f"Dashboard request failed: {response.status_code} - {response.text}")
else:
    print(f"Login failed: {response.status_code}")
