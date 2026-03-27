from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def fix_food_schema():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("=== FIXING FOOD SCHEMA ===\n")
        
        # 1. Check/Add price to food_items
        print("Checking food_items for 'price' column...")
        exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'food_items' AND column_name = 'price')")).scalar()
        if not exists:
            print("📝 Adding 'price' column to food_items...")
            conn.execute(text("ALTER TABLE food_items ADD COLUMN price INTEGER DEFAULT 0"))
            print("✅ Added 'price' column.")
        else:
            print("✅ 'price' column already exists.")

        # 2. Check food_categories
        print("\nChecking food_categories table...")
        exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'food_categories')")).scalar()
        if exists:
            print("✅ food_categories exists. Columns:")
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'food_categories' ORDER BY ordinal_position"))
            for row in result:
                print(f"  - {row[0]}")
        else:
            print("❌ food_categories DOES NOT EXIST!")

        conn.commit()
        print("\n=== DONE ===")

if __name__ == "__main__":
    fix_food_schema()
