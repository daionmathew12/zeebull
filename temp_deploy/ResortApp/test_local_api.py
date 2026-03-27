import requests

url = "http://127.0.0.1:8011/api/employees"
# We need to bypass authentication or provide a token.
# But 500 happens BEFORE 401 if it's a crash in the router setup? 
# Usually 401 happens in the dependency.
# If it's 500, it might be crashing in the dependency OR the handler.

# Let's try to get a token first.
# From previous turns, I know orchid_user/admin123 might be for DB, but what about API?
# Usually there's a /login or /token endpoint.

def test_api():
    try:
        # Try without auth first to see if it gives 401 or 500
        resp = requests.get(url)
        print(f"Status: {resp.status_code}")
        print(f"Content: {resp.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
