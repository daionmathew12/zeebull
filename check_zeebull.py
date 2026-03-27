import sys
import os
sys.path.append(r"c:\releasing\New Orchid\ResortApp")

from sqlalchemy import create_engine, MetaData
from sqlalchemy import text

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/zeebull_db"
engine = create_engine(DATABASE_URL)

def check():
    with engine.connect() as conn:
        print("Table Counts in zeebull_db:")
        meta = MetaData()
        meta.reflect(bind=engine)
        for table in meta.sorted_tables:
            try:
                count = conn.execute(text(f"SELECT count(*) FROM {table.name}")).scalar()
            except Exception as e:
                print(f"Error on {table.name}: {e}")
                continue
            
            if count > 0:
                print(f"{table.name}: {count}")

if __name__ == "__main__":
    check()
