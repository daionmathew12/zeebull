from app.database import engine
from sqlalchemy import text

def truncate_everything():
    with engine.connect() as conn:
        try:
            print("Fetching all table names...")
            # Get all tables in the public schema
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print("No tables found to truncate.")
                return

            table_list = ", ".join(tables)
            print(f"Truncating tables: {table_list}")
            
            # Use TRUNCATE CASCADE to handle foreign key dependencies
            conn.execute(text(f"TRUNCATE {table_list} CASCADE;"))
            conn.commit()
            print("Successfully truncated all tables.")
            
        except Exception as e:
            conn.rollback()
            print(f"Error during truncation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    truncate_everything()
