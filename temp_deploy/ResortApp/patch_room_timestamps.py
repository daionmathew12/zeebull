from app.database import engine
from sqlalchemy import text

def patch():
    with engine.connect() as conn:
        try:
           conn.execute(text("ALTER TABLE rooms ADD COLUMN housekeeping_updated_at TIMESTAMP"))
        except Exception as e: print(e)
        try:
           conn.execute(text("ALTER TABLE rooms ADD COLUMN last_maintenance_date DATE"))
        except Exception as e: print(e)
        
        # Initialize housekeeping timestamp
        try:
            conn.execute(text("UPDATE rooms SET housekeeping_updated_at = NOW() WHERE housekeeping_updated_at IS NULL"))
        except: pass
        
        conn.commit()
        print("Patched room timestamps.")

if __name__ == "__main__":
    patch()
