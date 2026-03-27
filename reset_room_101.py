from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("UPDATE rooms SET status = 'Available' WHERE number = '101'"))
        conn.commit()
        print("Room 101 reset to Available")
except Exception as e:
    print(f"Error: {e}")

sys.stdout.flush()
