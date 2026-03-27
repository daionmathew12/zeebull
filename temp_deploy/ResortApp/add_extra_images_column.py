from app.database import engine
from sqlalchemy import text

def add_extra_images_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE rooms ADD COLUMN extra_images TEXT"))
            conn.commit()
            print("Successfully added extra_images column to rooms table.")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e).lower():
                print("Column extra_images already exists.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_extra_images_column()
