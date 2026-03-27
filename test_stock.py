import urllib.request
import json

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3ODIwMTc1NjJ9.BcrhogSB8BxAj7muR1zwJodNzRFokRgmN6wObply93g'

def test_stock(branch_id, branch_name):
    url = 'http://localhost:8011/api/reports/inventory/stock-status'
    headers = {
        'X-Branch-ID': str(branch_id),
        'Authorization': f'Bearer {TOKEN}'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"\n=== Branch: {branch_name} (ID={branch_id}) ===")
            for item in data['stock_status']:
                print(f"  {item['item_name']}: stock={item['current_stock']} | value=Rs.{item['stock_value']:.2f} | status={item['status']}")
    except Exception as e:
        print(f'Error for branch {branch_name}: {e}')

test_stock(1, 'Trails')
test_stock(2, 'tr')
