#!/usr/bin/env python3
"""
Timestamp Migration Script
Adds started_at and completed_at columns to assigned_services, service_requests, and checkout_requests tables.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SQLALCHEMY_DATABASE_URL

def migrate_timestamps():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Timestamp Migration")
        print("=" * 60)
        print()

        tables_columns = [
            ("assigned_services", "started_at"),
            ("assigned_services", "completed_at"),
            ("service_requests", "started_at"),
            ("service_requests", "completed_at"),
            ("checkout_requests", "started_at"),
            ("checkout_requests", "completed_at"),
        ]

        for table, column in tables_columns:
            print(f"Checking {table}.{column}...")
            try:
                # Check if column exists is hard in raw SQL cross-db, so we just try to add it with IF NOT EXISTS if supported, 
                # or catch the error. PostgreSQL supports IF NOT EXISTS in ALTER TABLE ADD COLUMN in newer versions, 
                # but standard SQL doesn't always. 
                # Better approach for PG:
                # ALTER TABLE table_name ADD COLUMN IF NOT EXISTS column_name data_type;
                
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} TIMESTAMP WITHOUT TIME ZONE"))
                print(f"✓ Ensured {column} in {table}")
            except Exception as e:
                print(f"⚠️  Error adding {column} to {table}: {e}")
                # Use a specific check if "IF NOT EXISTS" syntax failed (e.g. older PG)
                # But GCP Postgres usually supports it.
        
        db.commit()
        print()
        print("=" * 60)
        print("✅ Timestamp migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate_timestamps()
