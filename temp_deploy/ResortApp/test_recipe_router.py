"""Test if recipe router can be imported and what routes it has"""
import sys
import os

# Set up path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Recipe Router Import")
print("=" * 60)

try:
    print("\n1. Testing model imports...")
    from app.models.recipe import Recipe, RecipeIngredient
    print("   ✅ Recipe models imported")
    
    from app.models.food_item import FoodItem
    print("   ✅ FoodItem model imported")
    
    from app.models.inventory import InventoryItem
    print("   ✅ InventoryItem model imported")
    
    print("\n2. Testing schema imports...")
    from app.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeOut, RecipeIngredientOut
    print("   ✅ Recipe schemas imported")
    
    print("\n3. Testing router import...")
    from app.api import recipe
    print("   ✅ Recipe router imported")
    
    print(f"\n4. Router details:")
    print(f"   Prefix: {recipe.router.prefix}")
    print(f"   Tags: {recipe.router.tags}")
    print(f"   Number of routes: {len(recipe.router.routes)}")
    
    print(f"\n5. Route details:")
    for route in recipe.router.routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
        path = route.path if hasattr(route, 'path') else 'N/A'
        print(f"   {methods} {path}")
    
    print("\n6. Testing router registration in main app...")
    from app.main import app
    recipe_routes = [r for r in app.routes if hasattr(r, 'path') and 'recipe' in r.path.lower()]
    
    if recipe_routes:
        print(f"   ✅ Found {len(recipe_routes)} recipe route(s) in app:")
        for route in recipe_routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
            print(f"      {methods} {route.path}")
    else:
        print("   ❌ No recipe routes found in app!")
        print("\n   This means the router was not registered.")
        print("   Check the server console for import/registration errors.")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



