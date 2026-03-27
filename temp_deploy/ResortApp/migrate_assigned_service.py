from sqlalchemy import text
from app.database import engine

def run_migration():
    print(f"Connecting to database using configured engine...")
    with engine.connect() as connection:
        # Check if column exists
        check_col = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='assigned_services' AND column_name='override_charges';
        """)
        result = connection.execute(check_col).fetchone()
        
        if not result:
            print("Adding override_charges column to assigned_services table...")
            try:
                # Add column
                connection.execute(text("ALTER TABLE assigned_services ADD COLUMN override_charges DOUBLE PRECISION;"))
                connection.commit()
                print("Column added successfully.")
            except Exception as e:
                print(f"Error adding column: {e}")
        else:
            print("Column override_charges already exists.")

if __name__ == "__main__":
    run_migration()
