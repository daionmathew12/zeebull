import os
import sys
from sqlalchemy import create_engine, inspect

# Add the project directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

# Load environment variables (mimicking app behavior)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

columns = inspector.get_columns('system_settings')
print("Columns in system_settings:")
for column in columns:
    print(f"- {column['name']}")
