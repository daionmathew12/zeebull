from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("--- Package Bookings Table columns ---")
        cols = conn.execute(text("""
            SELECT column_name FROM information_schema.columns WHERE table_name = 'package_bookings';
        """)).fetchall()
        for c in cols:
            print(c[0])
except Exception as e:
    print(f"Error: {e}")

sys.stdout.flush()
