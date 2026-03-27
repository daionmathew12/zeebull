"""
Test all accounting reports to ensure they're working
"""
import requests
import json

BASE_URL = "http://localhost:8011/api"

# You'll need to get a valid token from the browser
# Open DevTools -> Application -> Local Storage -> Look for 'token'
TOKEN = "YOUR_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

reports_to_test = [
    {
        "name": "Chart of Accounts",
        "endpoint": "/accounting/chart-of-accounts",
        "method": "GET"
    },
    {
        "name": "Journal Entries",
        "endpoint": "/accounting/journal-entries",
        "method": "GET"
    },
    {
        "name": "Trial Balance",
        "endpoint": "/accounting/trial-balance",
        "method": "GET",
        "params": {"start_date": "2024-01-01", "end_date": "2025-12-31"}
    },
    {
        "name": "GST Summary",
        "endpoint": "/accounting/gst-summary",
        "method": "GET",
        "params": {"start_date": "2024-01-01", "end_date": "2025-12-31"}
    },
    {
        "name": "Comprehensive Report",
        "endpoint": "/accounting/comprehensive-report",
        "method": "GET",
        "params": {"start_date": "2024-01-01", "end_date": "2025-12-31"}
    }
]

print("=" * 60)
print("ACCOUNTING REPORTS TEST")
print("=" * 60)

for report in reports_to_test:
    print(f"\n📊 Testing: {report['name']}")
    print(f"   Endpoint: {report['endpoint']}")
    
    try:
        url = BASE_URL + report['endpoint']
        params = report.get('params', {})
        
        if report['method'] == 'GET':
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.post(url, headers=headers, json=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Status: {response.status_code}")
            
            # Show some data info
            if isinstance(data, list):
                print(f"   📝 Records: {len(data)}")
            elif isinstance(data, dict):
                print(f"   📝 Keys: {list(data.keys())[:5]}")
        else:
            print(f"   ❌ FAILED - Status: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
