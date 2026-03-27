import requests

url = "https://teqmates.com/orchidapi/api/food-orders"
headers = {
    # I don't have a token, so I might get 401. Let's see if login endpoint is open or I can grab a token.
}
try:
    response = requests.get(url) 
    print(f"Status Code: {response.status_code}")
    print(response.json())
except Exception as e:
    print(e)
