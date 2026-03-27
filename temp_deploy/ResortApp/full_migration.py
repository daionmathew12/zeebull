from sqlalchemy import create_engine, text
import os

# Use DATABASE_URL from .env if possible
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb")

def run_migration():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # 1. Update stock_issues
        print("Migrating stock_issues table...")
        try:
            conn.execute(text("ALTER TABLE stock_issues ADD COLUMN IF NOT EXISTS booking_id INTEGER"))
            conn.execute(text("ALTER TABLE stock_issues ADD COLUMN IF NOT EXISTS guest_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_issues_booking_id ON stock_issues (booking_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_issues_guest_id ON stock_issues (guest_id)"))
            conn.execute(text("ALTER TABLE stock_issue_details ADD COLUMN IF NOT EXISTS is_damaged BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE stock_issue_details ADD COLUMN IF NOT EXISTS damage_notes TEXT"))
            conn.commit()
            print("Stock issues migrated.")
        except Exception as e:
            print(f"Error in stock_issues migration: {e}")
            conn.rollback()

        # 2. Update bookings
        print("Migrating bookings table...")
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS display_id VARCHAR"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bookings_display_id ON bookings (display_id)"))
            conn.commit()
            print("Bookings migrated.")
        except Exception as e:
            print(f"Error in bookings migration: {e}")
            conn.rollback()

if __name__ == "__main__":
    run_migration()
