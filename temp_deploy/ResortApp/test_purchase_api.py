import requests
import json

# Test creating a purchase with destination location
url = "http://localhost:8011/inventory/purchases"

data = {
    "purchase_number": "TEST-001",
    "vendor_id": 1,
    "purchase_date": "2025-12-05",
    "destination_location_id": 1,
    "status": "received",
    "payment_status": "pending",
    "details": [
        {
            "item_id": 1,
            "quantity": 5,
            "unit": "pcs",
            "unit_price": 100,
            "gst_rate": 18,
            "discount": 0
        }
    ]
}

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN_HERE"  # You'll need to get this from the browser
}

print("Sending request...")
print(json.dumps(data, indent=2))

# Note: This will fail without a valid token, but it will trigger the backend code
# and we can see the debug output in the terminal
