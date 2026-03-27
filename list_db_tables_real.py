from sqlalchemy import create_engine, inspect
import sys

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"

try:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("--- Existing Tables ---")
    for t in sorted(tables):
        print(t)
except Exception as e:
    print(f"Error: {e}")

sys.stdout.flush()
