"""Test recipe import"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing recipe import...")
try:
    print("1. Importing models...")
    from app.models.recipe import Recipe, RecipeIngredient
    print("   OK")
    
    print("2. Importing schemas...")
    from app.schemas.recipe import RecipeCreate, RecipeOut
    print("   OK")
    
    print("3. Importing router...")
    from app.api import recipe
    print("   OK")
    print(f"   Router prefix: {recipe.router.prefix}")
    print(f"   Routes: {len(recipe.router.routes)}")
    
    print("4. Testing app import...")
    from app.main import app
    recipe_routes = [r.path for r in app.routes if hasattr(r, 'path') and 'recipe' in r.path.lower()]
    print(f"   Recipe routes in app: {len(recipe_routes)}")
    if recipe_routes:
        for r in recipe_routes:
            print(f"      {r}")
    else:
        print("   WARNING: No recipe routes found!")
    
    print("\nSUCCESS: All imports work!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



