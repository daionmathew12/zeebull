from sqlalchemy import create_engine, inspect
import os

# Get DB URL from .env
with open(".env", "r") as f:
    for line in f:
        if line.startswith("DATABASE_URL="):
            db_url = line.split("=")[1].strip().strip('"')
            break

# Correct URL if it's using the old format
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
inspector = inspect(engine)

print("--- Columns in inventory_items ---")
columns = inspector.get_columns("inventory_items")
for column in columns:
    print(f"{column['name']}: {column['type']}")

print("\n--- Columns in inventory_categories ---")
columns = inspector.get_columns("inventory_categories")
for column in columns:
    print(f"{column['name']}: {column['type']}")
