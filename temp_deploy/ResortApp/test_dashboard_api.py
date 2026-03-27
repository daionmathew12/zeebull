"""
Test the dashboard API to see if department expenses are being calculated
"""
import requests
import json

# Test the dashboard summary endpoint
url = "http://localhost:8011/dashboard/summary?period=all"

try:
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    print("=" * 60)
    print("DASHBOARD API RESPONSE - DEPARTMENT KPIs")
    print("=" * 60)
    
    if "department_kpis" in data:
        dept_kpis = data["department_kpis"]
        
        if dept_kpis:
            print(f"\nFound {len(dept_kpis)} departments:\n")
            
            for dept_name, kpis in dept_kpis.items():
                print(f"{dept_name}:")
                print(f"  Assets:   ₹{kpis.get('assets', 0):,.2f}")
                print(f"  Income:   ₹{kpis.get('income', 0):,.2f}")
                print(f"  Expenses: ₹{kpis.get('expenses', 0):,.2f}")
                print(f"  Profit:   ₹{kpis.get('income', 0) - kpis.get('expenses', 0):,.2f}")
                print()
        else:
            print("\n⚠ No department KPIs found!")
    else:
        print("\n⚠ 'department_kpis' key not in response!")
    
    print("=" * 60)
    
    # Pretty print full response
    print("\nFull Response:")
    print(json.dumps(data, indent=2))
    
except Exception as e:
    print(f"❌ Error: {e}")
