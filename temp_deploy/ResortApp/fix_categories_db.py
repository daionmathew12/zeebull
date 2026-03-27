import sys
import os
from sqlalchemy import create_engine, text

# Add current directory to path to allow imports
sys.path.append(os.getcwd())

try:
    from app.database import SQLALCHEMY_DATABASE_URL
except ImportError:
    # Fallback if app.database cannot be imported
    print("Could not import app.database, using default sqlite")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./orchid.db"

def fix_categories_db():
    print(f"Connecting to database: {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            print("Attempting to add is_active column to inventory_categories...")
            conn.execute(text("ALTER TABLE inventory_categories ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
            conn.commit()
            print("Successfully added is_active column.")
        except Exception as e:
            print(f"Error (column might already exist): {e}")

if __name__ == "__main__":
    fix_categories_db()
