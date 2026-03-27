from app.database import SessionLocal
from sqlalchemy import text

def inspect_tables():
    db = SessionLocal()
    tables = ['employees', 'leaves', 'working_logs', 'users']
    try:
        for table in tables:
            print(f"Columns in {table}:")
            res = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
            for row in res:
                print(f"  {row.column_name}")
            print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_tables()
