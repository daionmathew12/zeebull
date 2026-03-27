import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path("c:/releasing/New Orchid/ResortApp/.env")
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not found in .env")
    sys.exit(1)

print(f"Connecting to: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)

columns_to_add = [
    ("image_url", "VARCHAR"),
    ("facebook", "VARCHAR"),
    ("instagram", "VARCHAR"),
    ("twitter", "VARCHAR"),
    ("linkedin", "VARCHAR"),
]

with engine.connect() as conn:
    # Check existing columns
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'branches'"))
    existing_columns = [row[0] for row in result]
    print(f"Existing columns: {existing_columns}")

    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            print(f"Adding column {col_name}...")
            try:
                conn.execute(text(f"ALTER TABLE branches ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Column {col_name} added successfully.")
            except Exception as e:
                print(f"Error adding column {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")

print("Migration complete.")
