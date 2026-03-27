"""
Add department column to inventory_transactions table
"""
from app.database import engine
from sqlalchemy import text

# Add the column
with engine.connect() as conn:
    try:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='inventory_transactions' 
            AND column_name='department'
        """))
        
        if result.fetchone():
            print("✓ Column 'department' already exists in inventory_transactions table")
        else:
            # Add the column
            conn.execute(text("""
                ALTER TABLE inventory_transactions 
                ADD COLUMN department VARCHAR
            """))
            conn.commit()
            print("✓ Successfully added 'department' column to inventory_transactions table")
    except Exception as e:
        print(f"✗ Error: {e}")
        conn.rollback()
