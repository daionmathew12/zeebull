"""
Add source_location_id and destination_location_id to inventory_transactions table
"""
from app.database import engine
from sqlalchemy import text

# Add the columns
with engine.connect() as conn:
    try:
        # Check if source_location_id exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='inventory_transactions' 
            AND column_name='source_location_id'
        """))
        
        if result.fetchone():
            print("✓ Column 'source_location_id' already exists in inventory_transactions table")
        else:
            # Add the column
            conn.execute(text("""
                ALTER TABLE inventory_transactions 
                ADD COLUMN source_location_id INTEGER REFERENCES locations(id)
            """))
            print("✓ Successfully added 'source_location_id' column to inventory_transactions table")

        # Check if destination_location_id exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='inventory_transactions' 
            AND column_name='destination_location_id'
        """))
        
        if result.fetchone():
            print("✓ Column 'destination_location_id' already exists in inventory_transactions table")
        else:
            # Add the column
            conn.execute(text("""
                ALTER TABLE inventory_transactions 
                ADD COLUMN destination_location_id INTEGER REFERENCES locations(id)
            """))
            print("✓ Successfully added 'destination_location_id' column to inventory_transactions table")
            
        conn.commit()
    except Exception as e:
        print(f"✗ Error: {e}")
        conn.rollback()
