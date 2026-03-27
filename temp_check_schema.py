import os
import sys

# Force UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.database import engine
from sqlalchemy import text

def check_schema():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'inventory_items';"))
        for row in result:
            print(row)
        
        result2 = conn.execute(text("SELECT id, name, branch_id FROM inventory_items;"))
        for row in result2:
            print(row)

if __name__ == "__main__":
    check_schema()
