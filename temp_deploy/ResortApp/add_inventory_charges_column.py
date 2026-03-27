
from app.database import engine
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE checkouts ADD COLUMN inventory_charges FLOAT DEFAULT 0.0"))
            conn.commit()
            print("Successfully added inventory_charges column.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("Column inventory_charges already exists.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_column()
