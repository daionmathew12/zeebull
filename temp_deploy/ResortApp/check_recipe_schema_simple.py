from sqlalchemy import create_engine, text

# Database connection for Orchid server
DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def check_recipe_columns():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("=== RECIPES TABLE ===")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'recipes' ORDER BY ordinal_position"))
        for row in result:
            print(f"- {row[0]}")
            
        print("\n=== RECIPE_INGREDIENTS TABLE ===")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'recipe_ingredients' ORDER BY ordinal_position"))
        for row in result:
            print(f"- {row[0]}")
            
if __name__ == "__main__":
    check_recipe_columns()
