import os
from sqlalchemy import text
from app.database import SessionLocal

def check_columns():
    db = SessionLocal()
    try:
        print("Columns in expenses table:")
        # For SQLite/Postgres/etc, information_schema is generally standard
        query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'expenses'")
        result = db.execute(query).fetchall()
        for row in result:
            print(f"- {row[0]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_columns()
