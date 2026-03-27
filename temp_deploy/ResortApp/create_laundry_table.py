from sqlalchemy import create_engine, text
from app.database import Base
from app.models.inventory import LaundryLog
import os

DATABASE_URL = "postgresql://postgres:qwerty123@localhost:5432/orchiddb"
engine = create_engine(DATABASE_URL)

def create_table():
    try:
        # Create table using metadata
        LaundryLog.__table__.create(engine)
        print("✅ LaundryLog table created successfully!")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        # Alternative: try creating with raw SQL if already exists or other issues
        try:
             print("Attempting to create with raw SQL...")
             with engine.connect() as conn:
                 conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS laundry_logs (
                        id SERIAL PRIMARY KEY,
                        item_id INTEGER NOT NULL REFERENCES inventory_items(id),
                        source_location_id INTEGER REFERENCES locations(id),
                        room_number VARCHAR,
                        quantity FLOAT NOT NULL,
                        status VARCHAR NOT NULL DEFAULT 'Incomplete Washing',
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        washed_at TIMESTAMP,
                        returned_at TIMESTAMP,
                        created_by INTEGER REFERENCES users(id),
                        notes TEXT
                    );
                 """))
                 conn.commit()
             print("✅ LaundryLog table verified/created with raw SQL!")
        except Exception as e2:
             print(f"❌ Raw SQL error: {e2}")

if __name__ == "__main__":
    create_table()
