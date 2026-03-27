from app.database import Base, engine
from app.models import *
from sqlalchemy import text
import sys

try:
    with engine.connect() as conn:
        print("Dropping all tables with CASCADE...")
        # Get all table names from Base.metadata
        for table in reversed(Base.metadata.sorted_tables):
            print(f"Dropping table {table.name}...")
            conn.execute(text(f'DROP TABLE IF EXISTS "{table.name}" CASCADE'))
        conn.commit()
        
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")
except Exception as e:
    print(f"Error resetting database: {e}")
    sys.exit(1)
