"""
Migration script to add last_used_at column to assigned_services table.
Run this script once to update your database schema.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print("=" * 60)
print("Adding last_used_at column to assigned_services table")
print("=" * 60)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    trans = conn.begin()
    try:
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'assigned_services' 
            AND column_name = 'last_used_at';
        """)
        result = conn.execute(check_query)
        exists = result.fetchone() is not None
        
        if exists:
            print("✓ Column 'last_used_at' already exists. Skipping migration.")
        else:
            # Add the column
            print("Adding last_used_at column...")
            conn.execute(text("""
                ALTER TABLE assigned_services 
                ADD COLUMN last_used_at TIMESTAMP NULL;
            """))
            print("✓ Column 'last_used_at' added successfully!")
        
        trans.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        trans.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



