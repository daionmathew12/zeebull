"""
Add is_deleted column to food_orders table
Run this script to add the missing column to the database
"""
from app.database import engine
from sqlalchemy import text

def add_is_deleted_column():
    """Add is_deleted column to food_orders table"""
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='food_orders' AND column_name='is_deleted'
            """))
            
            if result.fetchone() is None:
                # Column doesn't exist, add it
                conn.execute(text("""
                    ALTER TABLE food_orders 
                    ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE
                """))
                conn.commit()
                print("✓ Successfully added is_deleted column to food_orders table")
            else:
                print("✓ is_deleted column already exists in food_orders table")
                
    except Exception as e:
        print(f"✗ Error adding is_deleted column: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Adding is_deleted column to food_orders table...")
    add_is_deleted_column()
    print("Done!")
