from app.database import engine
from sqlalchemy import text

def add_refill_data_column():
    with engine.connect() as conn:
        # Add refill_data column to service_requests table
        conn.execute(text("""
            ALTER TABLE service_requests 
            ADD COLUMN IF NOT EXISTS refill_data TEXT
        """))
        conn.commit()
        print("Successfully added refill_data column to service_requests table")

if __name__ == "__main__":
    add_refill_data_column()
