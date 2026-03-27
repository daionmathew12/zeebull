from sqlalchemy import create_engine, text

# Database connection for Orchid server
DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def check_food_schema():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("=== FOOD_ITEMS TABLE SCHEMA ===")
        # Check if table exists
        exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'food_items')")).scalar()
        if not exists:
            print("❌ Table 'food_items' DOES NOT EXIST!")
            return
            
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'food_items' ORDER BY ordinal_position"))
        for row in result:
            print(f"- {row[0]}: {row[1]}")

if __name__ == "__main__":
    check_food_schema()
