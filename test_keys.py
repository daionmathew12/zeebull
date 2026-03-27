import requests
import json
try:
    res = requests.get('http://localhost:8011/bookings/?limit=5')
    print(res.text[:1000])
except Exception as e:
    print(f"Error: {e}")
