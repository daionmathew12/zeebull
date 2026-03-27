
from app.database import engine
from sqlalchemy import text

def add_status_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE expenses ADD COLUMN status VARCHAR DEFAULT 'Pending' NOT NULL"))
            conn.commit()
            print("Successfully added 'status' column to 'expenses' table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'status' already exists in 'expenses' table.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_status_column()
