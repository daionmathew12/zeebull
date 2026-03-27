
import os
import sys
from sqlalchemy import create_engine, MetaData, Table

# Add project root to path
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL

def check_columns():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    metadata = MetaData()
    try:
        table = Table('inventory_items', metadata, autoload_with=engine)
        print(f"Columns in 'inventory_items': {[c.name for c in table.columns]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
