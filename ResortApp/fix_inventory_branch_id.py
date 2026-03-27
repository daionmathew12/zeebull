
import os
import sys
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL

def fix_db_schema():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        print("Adding branch_id to inventory_categories...")
        try:
            conn.execute(text("ALTER TABLE inventory_categories ADD COLUMN branch_id INTEGER REFERENCES branches(id) DEFAULT 1"))
            conn.execute(text("UPDATE inventory_categories SET branch_id = 1 WHERE branch_id IS NULL"))
            conn.execute(text("ALTER TABLE inventory_categories ALTER COLUMN branch_id SET NOT NULL"))
            conn.commit()
            print("Successfully updated inventory_categories.")
        except Exception as e:
            print(f"Skipping inventory_categories: {e}")
            conn.rollback()

        print("Adding branch_id to inventory_items...")
        try:
            conn.execute(text("ALTER TABLE inventory_items ADD COLUMN branch_id INTEGER REFERENCES branches(id) DEFAULT 1"))
            conn.execute(text("UPDATE inventory_items SET branch_id = 1 WHERE branch_id IS NULL"))
            conn.execute(text("ALTER TABLE inventory_items ALTER COLUMN branch_id SET NOT NULL"))
            conn.commit()
            print("Successfully updated inventory_items.")
        except Exception as e:
            print(f"Skipping inventory_items: {e}")
            conn.rollback()

if __name__ == "__main__":
    fix_db_schema()
