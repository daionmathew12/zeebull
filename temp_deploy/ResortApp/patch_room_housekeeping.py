from app.database import engine
from sqlalchemy import text

def patch():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE rooms ADD COLUMN housekeeping_status VARCHAR DEFAULT 'Clean'"))
            print("Added housekeeping_status column")
        except Exception as e:
            print(f"Column housekeeping_status might already exist or error: {e}")
            
        conn.commit()

if __name__ == "__main__":
    patch()
