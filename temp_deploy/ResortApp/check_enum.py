from app.database import SessionLocal
from sqlalchemy import text

def check_enum():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT n.nspname as schema, t.typname as type, e.enumlabel as value FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'location_type'"))
        print("Allowed values for location_type:")
        for row in result:
            print(f"  {row.value}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_enum()
