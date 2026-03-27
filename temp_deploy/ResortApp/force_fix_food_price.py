from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def force_fix_food_price():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("=== FORCE FIX FOOD ITEMS ===")
        
        # Check specific column in public schema
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'food_items' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """))
        cols = [r[0] for r in result]
        print(f"Current columns: {cols}")
        
        if 'price' not in cols:
            print("📝 'price' is MISSING. Adding it now...")
            conn.execute(text("ALTER TABLE public.food_items ADD COLUMN price INTEGER DEFAULT 0"))
            print("✅ Added 'price' column.")
        else:
            print("✅ 'price' column is already present.")
            
        conn.commit()

if __name__ == "__main__":
    force_fix_food_price()
