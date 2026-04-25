from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path
import bcrypt

# Load .env
env_path = Path("c:/releasing/New Orchid/ResortApp/.env")
load_dotenv(dotenv_path=env_path)

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

email = "basil@gmail.com"
new_password = "admin123"

# Hash using bcrypt directly to avoid passlib version issues
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')

with engine.connect() as conn:
    print(f"Updating password for {email}...")
    result = conn.execute(
        text("UPDATE users SET hashed_password = :hashed WHERE email = :email"),
        {"hashed": hashed, "email": email}
    )
    conn.commit()
    print(f"Updated {result.rowcount} rows.")

    # Now verify login via API
    import requests
    try:
        response = requests.post(
            "http://localhost:8011/api/auth/login",
            json={"email": email, "password": new_password},
            timeout=5
        )
        print(f"\nLogin Verification:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error connecting to backend: {e}")
