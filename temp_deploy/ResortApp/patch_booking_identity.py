from app.database import engine
from sqlalchemy import text

def patch():
    with engine.connect() as conn:
        try:
           conn.execute(text("ALTER TABLE bookings ADD COLUMN is_id_verified BOOLEAN DEFAULT FALSE"))
        except Exception as e: print(e)
        try:
           conn.execute(text("ALTER TABLE bookings ADD COLUMN digital_signature_url VARCHAR"))
        except Exception as e: print(e)
        try:
           conn.execute(text("ALTER TABLE bookings ADD COLUMN special_requests VARCHAR"))
        except Exception as e: print(e)
        try:
           conn.execute(text("ALTER TABLE bookings ADD COLUMN preferences VARCHAR"))
        except Exception as e: print(e)
        
        conn.commit()
        print("Patched booking table.")

if __name__ == "__main__":
    patch()
