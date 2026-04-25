from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path("c:/releasing/New Orchid/ResortApp/.env")
load_dotenv(dotenv_path=env_path)

db_url = os.getenv("DATABASE_URL")
print(f"Connecting to: {db_url}")

engine = create_engine(db_url)
with engine.connect() as conn:
    query = """
        SELECT u.id, u.email, r.name as role_name, b.name as branch_name, u.is_active, u.is_superadmin
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        LEFT JOIN branches b ON u.branch_id = b.id
    """
    result = conn.execute(text(query))
    print("\nID | Email | Role | Branch | Active | Superadmin")
    print("-" * 80)
    for row in result:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
