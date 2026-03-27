
import os
import sys
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL

def query_info_schema():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'inventory_items'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            print(f"Direct columns in 'inventory_items' from info_schema:")
            for col in columns:
                print(f" - {col[0]} ({col[1]})")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    query_info_schema()
