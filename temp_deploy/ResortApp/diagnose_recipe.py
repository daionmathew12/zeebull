"""Comprehensive diagnostic script for recipe router"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Recipe Router Diagnostic")
print("=" * 70)

errors = []

# Test 1: Check if files exist
print("\n[1] Checking if files exist...")
files_to_check = [
    "app/models/recipe.py",
    "app/schemas/recipe.py",
    "app/api/recipe.py"
]
for file in files_to_check:
    if os.path.exists(file):
        print(f"   ✓ {file}")
    else:
        print(f"   ✗ {file} - MISSING!")
        errors.append(f"File missing: {file}")

# Test 2: Check model imports
print("\n[2] Testing model imports...")
try:
    from app.models.recipe import Recipe, RecipeIngredient
    print("   ✓ Recipe models imported successfully")
except Exception as e:
    print(f"   ✗ Recipe model import failed: {e}")
    errors.append(f"Model import error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check schema imports
print("\n[3] Testing schema imports...")
try:
    from app.schemas.recipe import RecipeCreate, RecipeOut, RecipeIngredientOut
    print("   ✓ Recipe schemas imported successfully")
except Exception as e:
    print(f"   ✗ Recipe schema import failed: {e}")
    errors.append(f"Schema import error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check router import
print("\n[4] Testing router import...")
try:
    from app.api import recipe
    print("   ✓ Recipe router imported successfully")
    print(f"   Router prefix: {recipe.router.prefix}")
    print(f"   Number of routes: {len(recipe.router.routes)}")
    for i, route in enumerate(recipe.router.routes, 1):
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods)
            print(f"   Route {i}: {methods} {route.path}")
except Exception as e:
    print(f"   ✗ Recipe router import failed: {e}")
    errors.append(f"Router import error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check if router is registered in app
print("\n[5] Testing router registration in app...")
try:
    from app.main import app
    
    recipe_routes = []
    all_routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            path = route.path
            all_routes.append(path)
            if 'recipe' in path.lower():
                recipe_routes.append(path)
    
    if recipe_routes:
        print(f"   ✓ Found {len(recipe_routes)} recipe route(s) in app:")
        for route in recipe_routes:
            print(f"      {route}")
    else:
        print("   ✗ No recipe routes found in app!")
        errors.append("Router not registered in app")
        print("\n   First 20 routes in app:")
        for route in all_routes[:20]:
            print(f"      {route}")
            
except Exception as e:
    print(f"   ✗ Error checking app routes: {e}")
    errors.append(f"App route check error: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
if errors:
    print("❌ DIAGNOSIS: Issues found!")
    print("\nErrors:")
    for error in errors:
        print(f"  - {error}")
    print("\nACTION REQUIRED:")
    print("1. Fix the errors listed above")
    print("2. Restart your backend server")
    print("3. Check the server console for error messages")
else:
    print("✅ DIAGNOSIS: All checks passed!")
    print("\nIf you're still getting 404 errors:")
    print("1. Make sure your backend server is running")
    print("2. Restart the server to load the new routes")
    print("3. Check the server console for startup messages")
print("=" * 70)



