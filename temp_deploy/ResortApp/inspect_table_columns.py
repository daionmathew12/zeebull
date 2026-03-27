from app.database import SessionLocal
from sqlalchemy import text

def inspect_table():
    db = SessionLocal()
    try:
        res = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'stock_issue_details'"))
        print("Columns in stock_issue_details:")
        for row in res:
            print(f"  {row.column_name}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_table()
