from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("--- Branches ---")
        branches = conn.execute(text("SELECT id, name, code FROM branches")).fetchall()
        for b in branches:
            print(f"ID={b[0]}, Name={b[1]}, Code={b[2]}")
            
        print("\n--- Rooms ---")
        rooms = conn.execute(text("SELECT id, number, branch_id, status FROM rooms")).fetchall()
        for r in rooms:
            print(f"ID={r[0]}, Number={r[1]}, BranchID={r[2]}, Status={r[3]}")
except Exception as e:
    print(f"Error: {e}")

sys.stdout.flush()
