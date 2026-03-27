from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Fix bookings table
    conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS is_id_verified BOOLEAN DEFAULT FALSE"))
    conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS package_preferences TEXT"))
    conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS digital_signature_url VARCHAR"))
    
    conn.commit()
    print("Local Bookings Schema Fixed")
