from app.database import SessionLocal
from sqlalchemy import text

def list_tables():
    db = SessionLocal()
    try:
        res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        print("Tables in database:")
        for row in res:
            print(f"  {row.table_name}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_tables()
