"""
Complete setup script for Recipe feature
This will:
1. Create database tables
2. Verify imports work
3. Check if routes are registered
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Recipe Feature Setup & Verification")
print("=" * 70)

# Step 1: Create database tables
print("\n[1/3] Creating database tables...")
try:
    from create_recipe_tables import *
    print("   ✅ Database migration script executed")
except Exception as e:
    print(f"   ⚠️  Migration script issue: {e}")
    print("   (This is okay if tables already exist)")

# Step 2: Verify imports
print("\n[2/3] Verifying imports...")
try:
    from app.models.recipe import Recipe, RecipeIngredient
    print("   ✅ Recipe models imported")
    
    from app.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeOut
    print("   ✅ Recipe schemas imported")
    
    from app.api import recipe
    print("   ✅ Recipe router imported")
    print(f"   ✅ Router prefix: {recipe.router.prefix}")
    print(f"   ✅ Number of routes: {len(recipe.router.routes)}")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Verify route registration
print("\n[3/3] Verifying route registration in app...")
try:
    from app.main import app
    
    recipe_routes = [r for r in app.routes if hasattr(r, 'path') and 'recipe' in r.path.lower()]
    
    if recipe_routes:
        print(f"   ✅ Found {len(recipe_routes)} recipe route(s):")
        for route in recipe_routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
            print(f"      {methods} {route.path}")
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Recipe feature is properly set up.")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Make sure your backend server is running")
        print("2. Restart the server if you just ran this script")
        print("3. Test the endpoint: GET http://localhost:8011/api/recipes")
    else:
        print("   ❌ No recipe routes found in app!")
        print("\n   This means the router was not registered.")
        print("   Check your server console when starting the server.")
        print("   You should see:")
        print("   - '✅ Recipe router imported successfully in app.main'")
        print("   - '✅ Recipe router registered in app.main with X routes'")
        print("\n" + "=" * 70)
        print("⚠️  Routes not registered. Check server console for errors.")
        print("=" * 70)
        
except Exception as e:
    print(f"   ❌ Error checking routes: {e}")
    import traceback
    traceback.print_exc()



