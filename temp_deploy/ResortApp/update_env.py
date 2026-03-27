import os

def update_env():
    content = """DATABASE_URL=postgresql+psycopg2://orchid_user:admin123@localhost/orchid_resort
SECRET_KEY=orchid-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
    print("Overwriting .env with CORRECT credentials...")
    with open(".env", "w") as f:
        f.write(content)
    print("✅ .env updated successfully.")

if __name__ == "__main__":
    update_env()
