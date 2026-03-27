from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/postgres"

try:
    engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        print("Recreating database orchiddb...")
        # Disconnect other users
        conn.execute(text("""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'orchiddb'
              AND pid <> pg_backend_pid();
        """))
        conn.execute(text("DROP DATABASE IF EXISTS orchiddb"))
        conn.execute(text("CREATE DATABASE orchiddb"))
        print("Database orchiddb recreated successfully.")
except Exception as e:
    print(f"Error: {e}")

sys.stdout.flush()
