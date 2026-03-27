import os
import sys
from sqlalchemy import create_engine, inspect
import re

# Add the project directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

models_dir = os.path.join(os.getcwd(), "ResortApp", "app", "models")
tables_to_check = []

for filename in os.listdir(models_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        with open(os.path.join(models_dir, filename), "r") as f:
            content = f.read()
            # Look for __tablename__ and branch_id
            tablename_match = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', content)
            if tablename_match:
                tablename = tablename_match.group(1)
                if "branch_id" in content:
                    tables_to_check.append(tablename)

print(f"Checking tables: {tables_to_check}")
for table in tables_to_check:
    try:
        columns = inspector.get_columns(table)
        column_names = [c['name'] for c in columns]
        if "branch_id" not in column_names:
            print(f"!!! MISSING branch_id in table: {table}")
        else:
            print(f"OK: {table}")
    except Exception as e:
        print(f"Error checking {table}: {e}")
