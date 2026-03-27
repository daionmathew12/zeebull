"""
Database Migration: Add Leave Balance Columns to Employees Table

This script adds leave balance tracking columns to the employees table.
Run this ONCE to update your database schema.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

def migrate_add_leave_balances():
    """Add leave balance columns to employees table"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='employees' AND column_name='paid_leave_balance'
        """))
        
        if result.fetchone():
            print("✅ Leave balance columns already exist. Skipping migration.")
            return
        
        print("📝 Adding leave balance columns to employees table...")
        
        # Add leave balance columns
        conn.execute(text("""
            ALTER TABLE employees 
            ADD COLUMN paid_leave_balance INTEGER DEFAULT 12,
            ADD COLUMN sick_leave_balance INTEGER DEFAULT 12,
            ADD COLUMN long_leave_balance INTEGER DEFAULT 5,
            ADD COLUMN wellness_leave_balance INTEGER DEFAULT 5
        """))
        
        conn.commit()
        print("✅ Successfully added leave balance columns!")
        
        # Update existing employees to have default leave balances
        conn.execute(text("""
            UPDATE employees 
            SET paid_leave_balance = 12,
                sick_leave_balance = 12,
                long_leave_balance = 5,
                wellness_leave_balance = 5
            WHERE paid_leave_balance IS NULL
        """))
        
        conn.commit()
        print("✅ Updated existing employees with default leave balances!")

def migrate_rename_leave_type():
    """Rename leave_type column to type in leaves table"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if old column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='leaves' AND column_name='leave_type'
        """))
        
        if not result.fetchone():
            print("✅ Column 'leave_type' doesn't exist or already renamed. Skipping.")
            return
        
        print("📝 Renaming leave_type to type in leaves table...")
        
        # Rename column
        conn.execute(text("""
            ALTER TABLE leaves 
            RENAME COLUMN leave_type TO type
        """))
        
        conn.commit()
        print("✅ Successfully renamed leave_type to type!")

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    print("=" * 50)
    
    try:
        migrate_add_leave_balances()
        print()
        migrate_rename_leave_type()
        print()
        print("=" * 50)
        print("✅ All migrations completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
