"""
Script to add display_id column to package_bookings table and backfill existing entries.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from sqlalchemy import text
from app.models.Package import PackageBooking
from app.utils.booking_id import format_display_id

def migrate():
    db = SessionLocal()
    try:
        # 1. Add column if it doesn't exist
        print("Checking for 'display_id' column in 'package_bookings'...")
        # Check if column already exists (handling both SQLite and PostgreSQL)
        try:
            # PostgreSQL check
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='package_bookings' AND column_name='display_id'
            """)
            result = db.execute(check_query).fetchone()
            already_exists = result is not None
        except:
            # SQLite fallback check
            try:
                check_query = text("PRAGMA table_info(package_bookings)")
                result = db.execute(check_query).fetchall()
                already_exists = any(row[1] == 'display_id' for row in result)
            except:
                already_exists = False
        
        if already_exists:
            print("Column 'display_id' already exists.")
        else:
            print("Adding 'display_id' column...")
            try:
                # Add the column
                alter_query = text("ALTER TABLE package_bookings ADD COLUMN display_id VARCHAR")
                db.execute(alter_query)
                db.commit()
                print("Successfully added 'display_id' column.")
            except Exception as e:
                print(f"Error adding column: {e}")
                db.rollback()
                # If it failed, maybe it exists but the check failed
        
        # 2. Backfill existing bookings
        print("Backfilling display_id for existing package bookings...")
        bookings = db.query(PackageBooking).filter(PackageBooking.display_id == None).all()
        print(f"Found {len(bookings)} bookings to update.")
        
        updated_count = 0
        for booking in bookings:
            branch_id = getattr(booking, 'branch_id', 1) or 1
            booking.display_id = format_display_id(booking.id, branch_id=branch_id, is_package=True)
            updated_count += 1
            if updated_count % 10 == 0:
                db.commit()
                print(f"Updated {updated_count} bookings...")
        
        db.commit()
        print(f"Successfully backfilled {updated_count} package bookings.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
