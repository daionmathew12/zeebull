from app.database import get_db
from sqlalchemy import text

db = next(get_db())

# Get local packages table schema
print("=== LOCAL PACKAGES TABLE SCHEMA ===")
result = db.execute(text("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name = 'packages' 
    ORDER BY ordinal_position
"""))

for row in result:
    print(f"{row[0]}: {row[1]} (nullable: {row[2]}, default: {row[3]})")
