from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

engine = create_engine(DATABASE_URL)
conn = engine.connect()

print("=== PACKAGES TABLE COLUMNS ===")
result = conn.execute(text("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'packages' 
    ORDER BY ordinal_position
"""))

columns = [r[0] for r in result]
for col in columns:
    print(f"  ✓ {col}")

print(f"\nTotal columns: {len(columns)}")

# Check specifically for status column
if 'status' in columns:
    print("\n✅ 'status' column exists!")
else:
    print("\n❌ 'status' column missing!")
