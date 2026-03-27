"""
Comprehensive API Test Script
Tests all major API endpoints to ensure they're working correctly
"""
import requests
import json
from datetime import datetime, date, timedelta

# Base URL for the API
BASE_URL = "http://localhost:8011"

# Test credentials
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(test_name, status, message=""):
    """Print test result with color coding"""
    if status == "PASS":
        print(f"{GREEN}✓ {test_name}: PASS{RESET} {message}")
    elif status == "FAIL":
        print(f"{RED}✗ {test_name}: FAIL{RESET} {message}")
    elif status == "SKIP":
        print(f"{YELLOW}⊘ {test_name}: SKIP{RESET} {message}")
    else:
        print(f"{BLUE}→ {test_name}{RESET} {message}")

def get_auth_token():
    """Login and get authentication token"""
    try:
        login_data = {
            "email": "admin@resort.com",
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print_test("Authentication", "PASS", f"Token obtained")
            return token
        else:
            print_test("Authentication", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print_test("Authentication", "FAIL", str(e))
        return None

def test_api(endpoint, method="GET", data=None, headers=None, test_name=None):
    """Generic API test function"""
    if test_name is None:
        test_name = f"{method} {endpoint}"
    
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "PATCH":
            response = requests.patch(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print_test(test_name, "FAIL", f"Unknown method: {method}")
            return None
        
        if response.status_code in [200, 201]:
            print_test(test_name, "PASS", f"Status: {response.status_code}")
            return response.json()
        else:
            print_test(test_name, "FAIL", f"Status: {response.status_code}, Response: {response.text[:200]}")
            return None
    except Exception as e:
        print_test(test_name, "FAIL", str(e))
        return None

def main():
    """Run all API tests"""
    print(f"\n{BLUE}{'='*80}")
    print(f"API Test Suite - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}{RESET}\n")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print(f"\n{RED}Cannot proceed without authentication token{RESET}\n")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Rooms API
    print(f"\n{BLUE}--- Testing Rooms API ---{RESET}")
    test_api("/api/rooms", headers=headers, test_name="Get All Rooms")
    
    # Test 2: Bookings API
    print(f"\n{BLUE}--- Testing Bookings API ---{RESET}")
    test_api("/api/bookings", headers=headers, test_name="Get All Bookings")
    test_api("/api/bookings/active", headers=headers, test_name="Get Active Bookings")
    
    # Test 3: Food Orders API
    print(f"\n{BLUE}--- Testing Food Orders API ---{RESET}")
    food_orders = test_api("/api/food-orders", headers=headers, test_name="Get All Food Orders")
    
    # Test 4: Food Items API
    print(f"\n{BLUE}--- Testing Food Items API ---{RESET}")
    test_api("/api/food-items", headers=headers, test_name="Get All Food Items")
    
    # Test 5: Food Categories API
    print(f"\n{BLUE}--- Testing Food Categories API ---{RESET}")
    test_api("/api/food-categories", headers=headers, test_name="Get All Food Categories")
    
    # Test 6: Services API
    print(f"\n{BLUE}--- Testing Services API ---{RESET}")
    test_api("/api/services", headers=headers, test_name="Get All Services")
    test_api("/api/assigned-services", headers=headers, test_name="Get Assigned Services")
    
    # Test 7: Service Requests API
    print(f"\n{BLUE}--- Testing Service Requests API ---{RESET}")
    service_requests = test_api("/api/service-requests", headers=headers, test_name="Get All Service Requests")
    
    # Test 8: Employees API
    print(f"\n{BLUE}--- Testing Employees API ---{RESET}")
    test_api("/api/employees", headers=headers, test_name="Get All Employees")
    
    # Test 9: Packages API
    print(f"\n{BLUE}--- Testing Packages API ---{RESET}")
    test_api("/api/packages", headers=headers, test_name="Get All Packages")
    test_api("/api/package-bookings", headers=headers, test_name="Get Package Bookings")
    
    # Test 10: Inventory API
    print(f"\n{BLUE}--- Testing Inventory API ---{RESET}")
    test_api("/api/inventory/items", headers=headers, test_name="Get Inventory Items")
    test_api("/api/inventory/categories", headers=headers, test_name="Get Inventory Categories")
    test_api("/api/inventory/vendors", headers=headers, test_name="Get Vendors")
    test_api("/api/inventory/locations", headers=headers, test_name="Get Locations")
    
    # Test 11: Checkout API
    print(f"\n{BLUE}--- Testing Checkout API ---{RESET}")
    test_api("/api/checkouts", headers=headers, test_name="Get All Checkouts")
    test_api("/api/active-rooms", headers=headers, test_name="Get Active Rooms for Checkout")
    
    # Test 12: Reports API
    print(f"\n{BLUE}--- Testing Reports API ---{RESET}")
    test_api("/api/reports/checkin-by-employee", headers=headers, test_name="Checkin by Employee Report")
    test_api("/api/reports/expenses", headers=headers, test_name="Expenses Report")
    test_api("/api/reports/room-bookings", headers=headers, test_name="Room Bookings Report")
    
    # Test 13: Accounting API
    print(f"\n{BLUE}--- Testing Accounting API ---{RESET}")
    test_api("/api/accounting/chart-of-accounts", headers=headers, test_name="Get Chart of Accounts")
    test_api("/api/accounting/journal-entries", headers=headers, test_name="Get Journal Entries")
    
    # Test 14: Notifications API
    print(f"\n{BLUE}--- Testing Notifications API ---{RESET}")
    test_api("/api/notifications", headers=headers, test_name="Get All Notifications")
    test_api("/api/notifications/unread", headers=headers, test_name="Get Unread Notifications")
    
    # Test 15: Users API
    print(f"\n{BLUE}--- Testing Users API ---{RESET}")
    test_api("/api/users", headers=headers, test_name="Get All Users")
    
    # Test 16: Roles API
    print(f"\n{BLUE}--- Testing Roles API ---{RESET}")
    test_api("/api/roles", headers=headers, test_name="Get All Roles")
    
    # Test 17: Expenses API
    print(f"\n{BLUE}--- Testing Expenses API ---{RESET}")
    test_api("/api/expenses", headers=headers, test_name="Get All Expenses")
    
    # Test 18: Health Check
    print(f"\n{BLUE}--- Testing Health Check ---{RESET}")
    test_api("/health", test_name="Health Check Endpoint")
    test_api("/", test_name="Root Endpoint")
    
    print(f"\n{BLUE}{'='*80}")
    print(f"API Test Suite Completed")
    print(f"{'='*80}{RESET}\n")

if __name__ == "__main__":
    main()
