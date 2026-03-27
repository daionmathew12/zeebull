import os
import sys
from sqlalchemy import create_engine, text

# Add the project directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

alter_query = """
ALTER TABLE system_settings ADD COLUMN branch_id INTEGER REFERENCES branches(id);
ALTER TABLE system_settings ADD CONSTRAINT uix_setting_key_branch UNIQUE (key, branch_id);
"""

with engine.connect() as conn:
    try:
        conn.execute(text(alter_query))
        conn.commit()
        print("Successfully added branch_id column and unique constraint to system_settings.")
    except Exception as e:
        print(f"Error: {e}")
