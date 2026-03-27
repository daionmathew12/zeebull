import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))
from sqlalchemy import text
from app.database import SessionLocal

def check_tables():
    db = SessionLocal()
    try:
        tables = ['header_banner', 'gallery', 'reviews', 'signature_experiences', 'plan_weddings', 'nearby_attractions', 'nearby_attraction_banners']
        for table in tables:
            print(f"=== {table} table columns ===")
            columns = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")).fetchall()
            cols = [c.column_name for c in columns]
            print(f"Columns: {', '.join(cols)}")
            if 'branch_id' in cols:
                print("HAS branch_id")
            else:
                print("MISSING branch_id")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_tables()
