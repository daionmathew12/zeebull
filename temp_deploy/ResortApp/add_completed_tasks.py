import os
from sqlalchemy import text
from app.database import SessionLocal, engine

def migrate():
    print("Starting migration...")
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE working_logs ADD COLUMN completed_tasks TEXT;"))
            print("Successfully added completed_tasks to working_logs table!")
        except Exception as e:
            if "already exists" in str(e) or "Duplicate column" in str(e):
                print("Column completed_tasks already exists!")
            else:
                print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
