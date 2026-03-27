import os
import sys

# Ensure current directory is in path for imports
sys.path.append(os.getcwd())

try:
    from app.database import SessionLocal
    from sqlalchemy import text
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def inspect_db():
    db = SessionLocal()
    try:
        # Check column types for 'locations' table
        print("--- Table Structure: locations ---")
        res = db.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'locations'
        """))
        for row in res:
            print(f"Column: {row.column_name}, Type: {row.data_type}, UDT: {row.udt_name}")
            
        # Check all custom types
        print("\n--- Custom Types ---")
        res = db.execute(text("""
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            ORDER BY t.typname, e.enumsortorder
        """))
        types = {}
        for row in res:
            if row.typname not in types:
                types[row.typname] = []
            types[row.typname].append(row.enumlabel)
            
        for t_name, labels in types.items():
            print(f"Type '{t_name}': {labels}")

        # Check existing location types
        print("\n--- Existing locations and their types ---")
        res = db.execute(text("SELECT id, name, location_type FROM locations"))
        for row in res:
            print(f"ID: {row.id}, Name: {row.name}, Type: {row.location_type}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
