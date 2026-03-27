
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_database():
    conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
    cur = conn.cursor()
    
    tables_to_fix = ['bookings', 'package_bookings']
    
    for table in tables_to_fix:
        print(f"Checking table: {table}")
        try:
            # Check if created_at exists
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'created_at';")
            if not cur.fetchone():
                print(f"Adding created_at to {table}...")
                cur.execute(f"ALTER TABLE {table} ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
                print(f"Successfully added created_at to {table}")
            else:
                print(f"created_at already exists in {table}")
        except Exception as e:
            print(f"Error fixing {table}: {e}")
            conn.rollback()
        else:
            conn.commit()
            
    cur.close()
    conn.close()
    print("Database fix complete!")

if __name__ == "__main__":
    fix_database()
