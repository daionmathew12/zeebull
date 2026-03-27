from sqlalchemy import create_engine, text

# Database connection for Orchid server
DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def fix_recipe_tables():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("=== RECREATING RECIPE TABLES ===\n")
        
        # Drop existing tables
        print("🗑️  Dropping recipe_ingredients table...")
        conn.execute(text("DROP TABLE IF EXISTS recipe_ingredients CASCADE"))
        
        print("🗑️  Dropping recipes table...")
        conn.execute(text("DROP TABLE IF EXISTS recipes CASCADE"))
        
        # Create recipes table
        print("📝 Creating recipes table...")
        conn.execute(text("""
            CREATE TABLE recipes (
                id SERIAL PRIMARY KEY,
                food_item_id INTEGER NOT NULL REFERENCES food_items(id),
                name VARCHAR NOT NULL,
                description TEXT,
                servings INTEGER DEFAULT 1,
                prep_time_minutes INTEGER,
                cook_time_minutes INTEGER,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
            )
        """))
        
        # Create recipe_ingredients table
        print("📝 Creating recipe_ingredients table...")
        conn.execute(text("""
            CREATE TABLE recipe_ingredients (
                id SERIAL PRIMARY KEY,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id),
                inventory_item_id INTEGER NOT NULL REFERENCES inventory_items(id),
                quantity FLOAT NOT NULL,
                unit VARCHAR NOT NULL,
                notes VARCHAR,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc')
            )
        """))
        
        # Create indexes
        print("📇 Creating indexes...")
        conn.execute(text("CREATE INDEX ix_recipes_id ON recipes (id)"))
        conn.execute(text("CREATE INDEX ix_recipe_ingredients_id ON recipe_ingredients (id)"))
        
        conn.commit()
        print("\n✅ RECIPE TABLES RECREATED SUCCESSFULLY!")

if __name__ == "__main__":
    fix_recipe_tables()
