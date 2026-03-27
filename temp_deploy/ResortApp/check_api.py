import time
import requests

token_res = requests.post('http://localhost:8011/api/auth/login', 
                          json={'email': 'admin@orchid.com', 'password': 'admin123'}, 
                          timeout=10)
token = token_res.json().get('access_token')

headers = {'Authorization': f'Bearer {token}', 'X-Branch-ID': 'all'}
endpoints = [
    '/inventory/categories?limit=100',
    '/inventory/vendors?limit=100',
    '/inventory/items?limit=100',
    '/inventory/purchases?limit=100',
    '/inventory/waste-logs?limit=100',
    '/inventory/locations?limit=100',
]

for ep in endpoints:
    start = time.time()
    try:
        r = requests.get(f'http://localhost:8011/api{ep}', headers=headers, timeout=10)
        elapsed = time.time() - start
        if r.ok:
            print(f"{ep}: status={r.status_code}, time={elapsed:.2f}s, count={len(r.json())}")
        else:
            print(f"{ep}: status={r.status_code}, time={elapsed:.2f}s, error={r.text[:200]}")
    except Exception as e:
        print(f"{ep}: TIMEOUT/ERROR after {time.time()-start:.2f}s: {e}")
