
import sys
import os
import asyncio
from httpx import ASGITransport, AsyncClient

# Set up paths
sys.path.append("/var/www/zeebull/ResortApp")
os.chdir("/var/www/zeebull/ResortApp")

from app.main import app

async def test_locations():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # We need a way to bypass get_current_user or provide a valid token
        # For debugging, I'll temporarily modify app/utils/auth.py to bypass if a certain header is present
        # Or I can just log in. Let's try log in.
        
        login_data = {"username": "admin", "password": "password123"} # Change to actual if known
        # Actually, I'll check user pwd in DB
        
        response = await client.get("/api/inventory/locations?limit=10000", headers={"X-Branch-Id": "2"})
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_locations())
