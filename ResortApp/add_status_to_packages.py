from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

def add_status_column():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE packages ADD COLUMN status VARCHAR DEFAULT 'active'"))
            print("Successfully added status column to packages table")
            conn.commit()
        except Exception as e:
            print(f"Error (column might already exist): {e}")

if __name__ == "__main__":
    add_status_column()
