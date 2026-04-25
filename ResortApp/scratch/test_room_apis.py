"""Test API responses for room 2 using the MANAGER token (branch_id=2)."""
import requests

# Manager token (basil@gmail.com, role=Manager, branch_id=2)
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJyb2xlIjoiTWFuYWdlciIsImJyYW5jaF9pZCI6MiwiaXNfc3VwZXJhZG1pbiI6ZmFsc2UsInBlcm1pc3Npb25zIjpbImRhc2hib2FyZDp2aWV3IiwiYm9va2luZ3M6dmlldyIsInJvb21zOnZpZXciLCJzZXJ2aWNlczp2aWV3Il0sImV4cCI6MTc4NTU4MzgwNX0.placeholder'

# Use the full token
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0LCJyb2xlIjoiTWFuYWdlciIsImJyYW5jaF9pZCI6MiwiaXNfc3VwZXJhZG1pbiI6ZmFsc2UsInBlcm1pc3Npb25zIjpbImRhc2hib2FyZDp2aWV3IiwiYWNjb3VudDp2aWV3IiwiYWNjb3VudDpjcmVhdGUiLCJhY2NvdW50OmVkaXQiLCJhY2NvdW50OmRlbGV0ZSIsImFjY291bnRfcmVwb3J0czp2aWV3IiwiYWNjb3VudF9jaGFydDp2aWV3IiwiYWNjb3VudF9jaGFydDpjcmVhdGUiLCJhY2NvdW50X2NoYXJ0OmVkaXQiLCJhY2NvdW50X2NoYXJ0OmRlbGV0ZSIsImFjY291bnRfam91cm5hbDp2aWV3IiwiYWNjb3VudF9qb3VybmFsOmNyZWF0ZSIsImFjY291bnRfam91cm5hbDplZGl0IiwiYWNjb3VudF9qb3VybmFsOmRlbGV0ZSIsImFjY291bnRfdHJpYWw6dmlldyIsImFjY291bnRfYXV0b19yZXBvcnQ6dmlldyIsImFjY291bnRfY29tcHJlaGVuc2l2ZV9yZXBvcnQ6dmlldyIsImFjY291bnRfZ3N0X3JlcG9ydHM6dmlldyIsImJvb2tpbmdzOnZpZXciLCJib29raW5nczpjcmVhdGUiLCJib29raW5nczplZGl0IiwiYm9va2luZ3M6ZGVsZXRlIiwicm9vbXM6dmlldyIsInJvb21zOmNyZWF0ZSIsInJvb21zOmVkaXQiLCJyb29tczpkZWxldGUiLCJzZXJ2aWNlczp2aWV3Iiwic2VydmljZXM6Y3JlYXRlIiwic2VydmljZXM6ZWRpdCIsInNlcnZpY2VzOmRlbGV0ZSIsInNlcnZpY2VzX2Rhc2hib2FyZDp2aWV3Iiwic2VydmljZXNfY3JlYXRlOnZpZXciLCJzZXJ2aWNlc19jcmVhdGU6Y3JlYXRlIiwic2VydmljZXNfY3JlYXRlOmVkaXQiLCJzZXJ2aWNlc19jcmVhdGU6ZGVsZXRlIiwic2VydmljZXNfYXNzaWduOnZpZXciLCJzZXJ2aWNlc19hc3NpZ246Y3JlYXRlIiwic2VydmljZXNfYXNzaWduOmVkaXQiLCJzZXJ2aWNlc19hc3NpZ246ZGVsZXRlIiwic2VydmljZXNfYXNzaWduZWQ6dmlldyIsInNlcnZpY2VzX3JlcXVlc3RzOnZpZXciLCJzZXJ2aWNlc19yZXF1ZXN0czplZGl0Iiwic2VydmljZXNfcmVwb3J0OnZpZXciLCJmb29kX29yZGVyczp2aWV3IiwiZm9vZF9vcmRlcnM6Y3JlYXRlIiwiZm9vZF9vcmRlcnM6ZWRpdCIsImZvb2Rfb3JkZXJzOmRlbGV0ZSIsImJpbGxpbmc6dmlldyIsImJpbGxpbmc6Y3JlYXRlIiwiYmlsbGluZzplZGl0IiwiYmlsbGluZzpkZWxldGUiLCJpbnZlbnRvcnk6dmlldyIsImludmVudG9yeV9pdGVtczp2aWV3IiwiZW1wbG95ZWVfbWFuYWdlbWVudDp2aWV3Iiwic2V0dGluZ3Nfc3lzdGVtOnZpZXciXSwiZXhwIjoxNzg1NTgzODA1fQ.mgyG18V5F6BBeCD4Qm0te50ME642b8t5SOUoDYSzuu0'

H = {'Authorization': 'Bearer ' + TOKEN}
BASE = 'http://127.0.0.1:8011/api'

print("=== BOOKINGS for room 2 (manager, branch=2) ===")
r = requests.get(BASE + '/bookings', params={'room_id': 2}, headers=H)
print("Status:", r.status_code)
if r.ok:
    d = r.json()
    print("Total:", d.get('total'), "| Bookings:", len(d.get('bookings', [])))
    for b in d.get('bookings', []):
        print(" ->", b.get('guest_name'), b.get('status'))
else:
    print("Error:", r.text[:300])

print()
print("=== SERVICE REQUESTS for room 2 (manager, branch=2) ===")
r2 = requests.get(BASE + '/service-requests', params={'room_id': 2}, headers=H)
print("Status:", r2.status_code)
if r2.ok:
    items = r2.json()
    print("Count:", len(items))
    for s in items:
        print(" -> type:", s.get('type'), "status:", s.get('status'))
else:
    print("Error:", r2.text[:300])
