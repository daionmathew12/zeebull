from sqlalchemy import text
from app.database import engine

def migrate():
    with engine.connect() as conn:
        print(f"Using database engine: {engine.url}")
        
        # Check for working_logs table
        # Table name might vary by case in some DBs, but standard is lowercase
        new_columns = [
            ("clock_in_image", "VARCHAR"),
            ("clock_out_image", "VARCHAR")
        ]
        
        for col_name, col_type in new_columns:
            print(f"Attempting to add {col_name} to working_logs...")
            try:
                # We use a raw SQL execution that works for both Postgres and SQLite for column addition
                conn.execute(text(f"ALTER TABLE working_logs ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Successfully added {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"Column {col_name} already exists.")
                else:
                    print(f"Error adding {col_name}: {e}")

if __name__ == "__main__":
    migrate()
