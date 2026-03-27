import requests

# Test the API endpoint
response = requests.get(
    "http://localhost:8011/api/inventory/locations/18/items",
    headers={"Authorization": "Bearer YOUR_TOKEN"}  # You'll need to replace with actual token
)

print("Status Code:", response.status_code)
print("\nResponse:")
import json
print(json.dumps(response.json(), indent=2))
