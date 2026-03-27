
from sqlalchemy import create_all, create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost/resort_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_db():
    db = SessionLocal()
    try:
        # Check bookings
        result = db.execute("SELECT count(*) FROM bookings").fetchone()
        print(f"Regular Bookings: {result[0]}")
        
        # Check package bookings
        result = db.execute("SELECT count(*) FROM package_bookings").fetchone()
        print(f"Package Bookings: {result[0]}")
        
        # Check branches
        result = db.execute("SELECT id, name FROM branches").fetchall()
        print(f"Branches: {result}")
        
        # Check bookings per branch
        result = db.execute("SELECT branch_id, count(*) FROM bookings GROUP BY branch_id").fetchall()
        print(f"Bookings per branch: {result}")
        
        # Check package bookings per branch
        result = db.execute("SELECT branch_id, count(*) FROM package_bookings GROUP BY branch_id").fetchall()
        print(f"Package Bookings per branch: {result}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
