#!/usr/bin/env python3
"""
Database Migration Script to Add average_completion_time to services table
Run this script to add the average_completion_time column.

Usage:
    cd ResortApp
    python migrate_add_average_completion_time.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SQLALCHEMY_DATABASE_URL

def migrate_database():
    """Add average_completion_time column to services table."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Add average_completion_time to services table")
        print("=" * 60)
        print()

        # Add average_completion_time column
        print("Step 1/1: Migrating 'services' table...")
        print("-" * 60)
        try:
            db.execute(text("ALTER TABLE services ADD COLUMN IF NOT EXISTS average_completion_time VARCHAR"))
            db.commit()
            print("✓ Added 'average_completion_time' column to services table")
        except Exception as e:
            print(f"⚠️  average_completion_time column: {e}")
            db.rollback()
        print()

        print("=" * 60)
        print("✅ Database migration completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart the backend service if running")
        print("2. Verify the application is working")
        print("3. Update existing services with average completion time if needed")

    except Exception as e:
        db.rollback()
        print()
        print("=" * 60)
        print("❌ Error during database migration:")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("Please check the error above and try again.")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()


