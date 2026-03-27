"""
Migration script to create Recipe and RecipeIngredient tables.
Run this script once to update your database schema.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print("=" * 60)
print("Creating Recipe and RecipeIngredient tables")
print("=" * 60)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    trans = conn.begin()
    try:
        # Check if tables already exist
        check_recipes = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'recipes';
        """))
        recipes_exists = check_recipes.fetchone() is not None
        
        check_ingredients = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'recipe_ingredients';
        """))
        ingredients_exists = check_ingredients.fetchone() is not None
        
        if recipes_exists and ingredients_exists:
            print("✓ Tables 'recipes' and 'recipe_ingredients' already exist. Skipping migration.")
        else:
            # Read and execute SQL file
            sql_file = Path(__file__).parent / "create_recipe_tables.sql"
            if sql_file.exists():
                with open(sql_file, 'r') as f:
                    sql_content = f.read()
                # Execute each statement
                for statement in sql_content.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        try:
                            conn.execute(text(statement))
                        except Exception as e:
                            if 'already exists' not in str(e).lower():
                                print(f"Warning: {e}")
                print("✓ Tables created successfully!")
            else:
                print("ERROR: create_recipe_tables.sql not found")
                sys.exit(1)
        
        trans.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        trans.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



