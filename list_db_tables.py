import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))
from sqlalchemy import text
from app.database import SessionLocal

def list_tables():
    db = SessionLocal()
    try:
        print("=== All tables ===")
        tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        for t in tables:
            print(t.table_name)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_tables()
