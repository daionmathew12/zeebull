"""
Database migration script to add is_payable and is_paid columns to stock_issue_details table
"""
import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def run_migration():
    # Get database URL from environment
    db_url = os.getenv("DATABASE_URL")
    
    # Parse the URL to get connection parameters
    # Format: postgresql://user:password@host:port/database
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if not match:
        print("Error: Could not parse database URL")
        return False
    
    user, password, host, port, database = match.groups()
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Run migration
        sql = """
        ALTER TABLE stock_issue_details 
        ADD COLUMN IF NOT EXISTS is_payable BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS is_paid BOOLEAN DEFAULT FALSE;
        """
        
        print("Running migration...")
        cursor.execute(sql)
        print("✓ Migration completed successfully!")
        
        # Verify columns were added
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'stock_issue_details' 
            AND column_name IN ('is_payable', 'is_paid');
        """)
        
        results = cursor.fetchall()
        print("\nVerification - Columns in stock_issue_details:")
        for row in results:
            print(f"  - {row[0]}: {row[1]} (default: {row[2]})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error running migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n✓ Database migration completed successfully!")
        print("You can now refresh your browser to see the inventory items.")
    else:
        print("\n✗ Migration failed. Please check the error above.")
