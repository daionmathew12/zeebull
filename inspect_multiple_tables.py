import os
import sys
from sqlalchemy import create_engine, inspect

# Add the project directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

tables = ['employees', 'leaves', 'attendances', 'working_logs', 'system_settings']
for table in tables:
    columns = inspector.get_columns(table)
    print(f"Columns in {table}:")
    for column in columns:
        print(f"- {column['name']}")
    print()
