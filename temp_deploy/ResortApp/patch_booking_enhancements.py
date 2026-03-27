from app.database import engine
from sqlalchemy import text, inspect

def patch_database():
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # 1. Add 'source' to bookings
        # inspector.get_columns('bookings') might require connection? usually engine is enough.
        columns = [c['name'] for c in inspector.get_columns('bookings')]
        if 'source' not in columns:
            print("Adding 'source' column to bookings table...")
            conn.execute(text("ALTER TABLE bookings ADD COLUMN source VARCHAR DEFAULT 'Direct'"))
            print("Added 'source' column.")
        else:
            print("'source' column already exists.")

        # 2. Add 'package_name' to bookings
        if 'package_name' not in columns:
            print("Adding 'package_name' column to bookings table...")
            conn.execute(text("ALTER TABLE bookings ADD COLUMN package_name VARCHAR DEFAULT NULL"))
            print("Added 'package_name' column.")
        
        conn.commit()
        print("Database patch completed successfully.")

if __name__ == "__main__":
    patch_database()
