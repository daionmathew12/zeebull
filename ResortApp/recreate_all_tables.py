import sys
import os
from sqlalchemy import text

# Add the parent directory to sys.path to import the app
sys.path.append(os.getcwd())

from app.database import Base, engine
from app.models import *  # Ensure all models are loaded

def recreate_tables():
    print("WARNING: This will drop ALL tables in the database using CASCADE!")
    print(f"Database URL: {engine.url}")
    
    try:
        with engine.connect() as conn:
            print("Dropping public schema with CASCADE...")
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            # Optionally grant to specific user if known, but public is usually enough
            conn.commit()
            
        print("Creating all tables from models...")
        Base.metadata.create_all(bind=engine)
        print("Success: All tables recreated successfully.")
    except Exception as e:
        print(f"Error during recreation: {e}")
        # Try metadata.drop_all as last resort if schema drop failed
        try:
           print("Falling back to metadata.drop_all(checkfirst=False)...")
           Base.metadata.drop_all(bind=engine)
           Base.metadata.create_all(bind=engine)
           print("Success using fallback.")
        except Exception as e2:
           print(f"Fallback also failed: {e2}")
           sys.exit(1)

if __name__ == "__main__":
    recreate_tables()
