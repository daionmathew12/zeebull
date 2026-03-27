from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def check_inv_schema():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("=== INVENTORY_ITEMS TABLE ===")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'inventory_items' ORDER BY ordinal_position"))
        columns = [row[0] for row in result]
        for col in columns:
            print(f"- {col}")
            
        if 'unit_price' in columns:
            print("✅ unit_price exists")
        else:
            print("❌ unit_price MISSING")

if __name__ == "__main__":
    check_inv_schema()
