import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path to import app modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Adding booking_id and guest_id columns to stock_issues table...")
        try:
            conn.execute(text("ALTER TABLE stock_issues ADD COLUMN IF NOT EXISTS booking_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_issues_booking_id ON stock_issues (booking_id)"))
            conn.execute(text("ALTER TABLE stock_issues ADD COLUMN IF NOT EXISTS guest_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_issues_guest_id ON stock_issues (guest_id)"))
            conn.commit()
            print("Successfully updated stock_issues table.")
        except Exception as e:
            print(f"Error updating table: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
