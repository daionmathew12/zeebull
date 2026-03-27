"""Direct test of recipe router"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing recipe router import...")
try:
    # Test each import step by step
    print("1. Testing models...")
    from app.models.recipe import Recipe, RecipeIngredient
    print("   OK")
    
    print("2. Testing schemas...")
    from app.schemas.recipe import RecipeCreate, RecipeOut
    print("   OK")
    
    print("3. Testing router import...")
    from app.api import recipe
    print(f"   OK - Router prefix: {recipe.router.prefix}")
    print(f"   Routes: {len(recipe.router.routes)}")
    
    print("4. Testing router registration...")
    from app.main import app
    
    # Check all routes
    all_routes = [r.path for r in app.routes if hasattr(r, 'path')]
    recipe_routes = [r for r in all_routes if 'recipe' in r.lower()]
    
    print(f"   Total routes: {len(all_routes)}")
    print(f"   Recipe routes: {len(recipe_routes)}")
    
    if recipe_routes:
        print("   ✅ Recipe routes found:")
        for route in recipe_routes:
            print(f"      {route}")
    else:
        print("   ❌ No recipe routes found!")
        print("\n   First 10 routes:")
        for route in all_routes[:10]:
            print(f"      {route}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()



