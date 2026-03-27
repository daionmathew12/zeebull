"""
Migration script to add department column to expenses table
"""
from app.database import engine
from sqlalchemy import text

def add_department_column():
    """Add department column to expenses table if it doesn't exist"""
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='expenses' AND column_name='department'
            """))
            
            if result.fetchone() is None:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE expenses 
                    ADD COLUMN department VARCHAR
                """))
                conn.commit()
                print("✅ Added 'department' column to expenses table")
            else:
                print("ℹ️  'department' column already exists")
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_department_column()

