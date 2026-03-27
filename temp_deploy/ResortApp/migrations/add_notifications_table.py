"""
Migration script to add notifications table to the database.
Run this script to create the notifications table.
"""

import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models.notification import Notification

def run_migration():
    """Create the notifications table"""
    try:
        print("Creating notifications table...")
        # Create only the notifications table
        Notification.__table__.create(bind=engine, checkfirst=True)
        print("✓ Notifications table created successfully!")
    except Exception as e:
        print(f"✗ Error creating notifications table: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_migration()
