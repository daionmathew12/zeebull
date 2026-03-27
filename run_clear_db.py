from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"

sql_file_path = r"c:\releasing\New Orchid\ResortApp\clear_all_data.sql"

try:
    engine = create_engine(DATABASE_URL)
    with open(sql_file_path, 'r') as file:
        sql_script = file.read()
    
    # The script uses BEGIN; ... COMMIT; so we can execute it as is if we use a connection.
    # However, TRUNCATE ... CASCADE might be better run in a single transaction.
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # SQLAlchemy text() might have issues with multiple statements, but let's try.
            # Sometimes it's better to split by ; or use raw connection.
            raw_conn = conn.connection
            with raw_conn.cursor() as cursor:
                cursor.execute(sql_script)
            trans.commit()
            print("Database cleared successfully.")
        except Exception as e:
            trans.rollback()
            print(f"Error during clearing: {e}")
            
except Exception as e:
    print(f"Connection error: {e}")

sys.stdout.flush()
