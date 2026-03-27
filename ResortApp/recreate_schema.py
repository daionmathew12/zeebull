import sys
import os
from sqlalchemy import text
# Add current directory to path to import app
sys.path.append(os.getcwd())

from app.database import Base, engine, SQLALCHEMY_DATABASE_URL
from app.models import * # Ensure all models are imported

def recreate():
    print(f"Connecting to: {SQLALCHEMY_DATABASE_URL[:50]}...")
    
    print("Dropping public schema...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        
        # Only grant to orchid_user if it's likely a server environment
        if "orchid_user" in SQLALCHEMY_DATABASE_URL:
            try:
                conn.execute(text("GRANT ALL ON SCHEMA public TO orchid_user"))
            except Exception as e:
                print(f"Warning: Could not grant to orchid_user: {e}")
        
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        conn.commit()
    
    print("Creating all tables via SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    recreate()
