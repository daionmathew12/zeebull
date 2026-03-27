import requests

# Superadmin token we created earlier
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdXBlcmFkbWluQGdtYWlsLmNvbSIsInVzZXJfaWQiOjEsInJvbGUiOiJzdXBlcmFkbWluIiwiYnJhbmNoX2lkIjpudWxsLCJpc19zdXBlcmFkbWluIjp0cnVlLCJwZXJtaXNzaW9ucyI6W10sImV4cCI6MTgwNDkxNjEwOH0.vH3FLnRu63K9SrrPTL-PsJ9b5NoEf3wgryGfpqc8hiM'

BASE_URL = "http://localhost:8011"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# List of endpoints to test (gathered from router prefixes)
endpoints = [
    # Front Office
    "/api/reports/front-office/daily-arrival",
    "/api/reports/front-office/daily-departure",
    "/api/reports/front-office/in-house",
    "/api/reports/front-office/collection",
    
    # Housekeeping
    "/api/reports/housekeeping/status",
    "/api/reports/housekeeping/tasks",
    
    # F&B
    "/api/reports/restaurant/daily-sales",
    "/api/reports/restaurant/item-sales",
    "/api/reports/restaurant/bill-summary",
    
    # Inventory & Accounts
    "/api/reports/inventory/stock-status",
    "/api/reports/purchase-register",
    "/api/reports/expenses",
    "/api/reports/vendor-payments",
    "/api/reports/waste-log",
    
    # Security & HR
    "/api/reports/security/visitor-log",
    "/api/reports/hr/attendance",
    "/api/reports/hr/payroll-summary",
    
    # Comprehensive & GST
    "/api/reports/comprehensive/inventory-by-category",
    "/api/reports/gst/sales"
]

print("Testing all report endpoints for 500 errors...")
success = 0
errors = 0

for endpoint in endpoints:
    url = f"{BASE_URL}{endpoint}"
    try:
        # Test branch view (Trails)
        headers_branch = {**HEADERS, "X-Branch-ID": "1"}
        res1 = requests.get(url, headers=headers_branch)
        
        # Test enterprise view (All branches)
        headers_ent = {**HEADERS, "X-Branch-ID": "all"}
        res2 = requests.get(url, headers=headers_ent)
        
        status1 = res1.status_code
        status2 = res2.status_code
        
        if status1 == 200 and status2 == 200:
            print(f"✅ {endpoint} OK")
            success += 1
        else:
            print(f"❌ {endpoint} FAILED (Branch: {status1}, Enterprise: {status2})")
            if status1 != 200: print(f"   Branch Error: {res1.text[:200]}")
            if status2 != 200: print(f"   Enterprise Error: {res2.text[:200]}")
            errors += 1
    except Exception as e:
        print(f"❌ {endpoint} EXCEPTION: {e}")
        errors += 1

print(f"\\nTotal: {len(endpoints)}, Success: {success}, Errors: {errors}")
