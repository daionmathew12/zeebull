import requests
from requests.auth import HTTPBasicAuth
# Since we don't have token readily, let's just use FastAPI dependency override or TestClient
from fastapi.testclient import TestClient
from main import app
from app.utils.auth import get_current_user

# We can bypass auth for local test
client = TestClient(app)
response = client.get("/service-requests?room_id=6")
print(response.status_code)
print(response.json())
