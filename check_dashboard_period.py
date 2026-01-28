import requests
import json

# Login
login_url = "https://teqmates.com/orchidapi/api/auth/login"
login_payload = {"email": "admin@orchid.com", "password": "admin123"}

response = requests.post(login_url, json=login_payload)
if response.status_code == 200:
    token = response.json().get("access_token")
    
    # Get dashboard summary with period=day
    dashboard_url = "https://teqmates.com/orchidapi/api/dashboard/summary?period=day"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(dashboard_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("=== BACKEND DASHBOARD DATA (period=day) ===")
        print(json.dumps(data, indent=2))
        print(f"\n=== KEY METRICS ===")
        print(f"total_revenue: {data.get('total_revenue', 'NOT FOUND')}")
        print(f"total_expenses: {data.get('total_expenses', 'NOT FOUND')}")
        print(f"revenue: {data.get('revenue', 'NOT FOUND')}")
        print(f"expenses: {data.get('expenses', 'NOT FOUND')}")
    else:
        print(f"Dashboard request failed: {response.status_code} - {response.text}")
else:
    print(f"Login failed: {response.status_code}")
