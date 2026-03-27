"""
Migration script to add recipient_id column to notifications table
"""
from app.database import engine
from sqlalchemy import text

def add_recipient_id_column():
    """Add recipient_id column to notifications table if it doesn't exist"""
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='notifications' AND column_name='recipient_id'
            """))
            
            if result.fetchone() is None:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE notifications 
                    ADD COLUMN recipient_id INTEGER REFERENCES users(id)
                """))
                conn.commit()
                print("✅ Added 'recipient_id' column to notifications table")
            else:
                print("ℹ️  'recipient_id' column already exists")
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_recipient_id_column()
