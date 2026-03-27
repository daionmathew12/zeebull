import sys
import os
sys.path.append(r"c:\releasing\New Orchid\ResortApp")

from app.database import SessionLocal, engine
from app.models import *
from app.database import Base
from sqlalchemy import text

def check():
    db = SessionLocal()
    print("Table Counts:")
    for table in Base.metadata.sorted_tables:
        try:
            count = db.execute(text(f"SELECT count(*) FROM {table.name}")).scalar()
            if count > 0:
                print(f"{table.name}: {count}")
        except Exception as e:
            print(f"Error on {table.name}: {e}")

if __name__ == "__main__":
    check()
