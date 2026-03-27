from sqlalchemy import create_engine, text

# Database connection for Orchid server
DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def check_recipe_schema():
    """Check schema for recipe-related tables"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("=== RECIPE SCHEMA CHECK ===\n")
        
        tables = ['recipes', 'recipe_ingredients', 'inventory_items', 'food_items']
        
        for table in tables:
            print(f"checking table: {table}")
            
            # Check if table exists
            exists = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                )
            """)).scalar()
            
            if not exists:
                print(f"❌ Table '{table}' DOES NOT EXIST!")
                continue
            
            print(f"✅ Table '{table}' exists")
            
            # Get columns
            result = conn.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position
            """))
            
            print(f"   Columns:")
            for row in result:
                print(f"   - {row[0]}: {row[1]} (nullable: {row[2]})")
            print("")

if __name__ == "__main__":
    check_recipe_schema()
