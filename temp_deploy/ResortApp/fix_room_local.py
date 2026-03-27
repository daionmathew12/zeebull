from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS housekeeping_status VARCHAR DEFAULT 'Clean'"))
    conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS housekeeping_updated_at TIMESTAMP"))
    conn.execute(text("ALTER TABLE rooms ADD COLUMN IF NOT EXISTS last_maintenance_date DATE"))
    conn.commit()
    print("Local Room Schema Fixed")
