import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))
from sqlalchemy import text
from app.database import SessionLocal

def list_branches():
    db = SessionLocal()
    try:
        print("=== Branches in DB ===")
        res = db.execute(text("SELECT id, name FROM branches")).fetchall()
        for r in res:
            print(f"ID={r.id}, Name='{r.name}'")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_branches()
