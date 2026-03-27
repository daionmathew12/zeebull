"""
Clear All Recipes
This script removes all recipes and their ingredients.
"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("=" * 80)
    print("CLEARING ALL RECIPES")
    print("=" * 80)
    print("\nThis will delete:")
    print("  - All recipes")
    print("  - All recipe ingredients")
    print("=" * 80)
    
    # Confirm
    response = input("\nAre you sure you want to proceed? (type 'YES' to confirm): ")
    if response != "YES":
        print("Operation cancelled.")
        db.close()
        exit()
    
    print("\nStarting cleanup...")
    
    # 1. Clear recipe ingredients first (foreign key to recipes)
    print("\n[1/2] Clearing recipe ingredients...")
    db.execute(text("DELETE FROM recipe_ingredients"))
    print("  ✓ Recipe ingredients cleared")
    
    # 2. Clear recipes
    print("[2/2] Clearing recipes...")
    db.execute(text("DELETE FROM recipes"))
    print("  ✓ Recipes cleared")
    
    # Commit all changes
    db.commit()
    
    print("\n" + "=" * 80)
    print("✓ ALL RECIPES CLEARED SUCCESSFULLY!")
    print("=" * 80)
    print("\nAll recipes and their ingredients have been removed.")
    print("You can now create new recipes from scratch.")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    db.rollback()
    print("Changes rolled back. Database unchanged.")
finally:
    db.close()
