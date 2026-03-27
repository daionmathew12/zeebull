from app.schemas.recipe import RecipeCreate

print("Testing RecipeCreate schema validation...")
try:
    # Test with empty string for cook_time_minutes
    obj = RecipeCreate(
        food_item_id=1, 
        name="Test Recipe", 
        cook_time_minutes="",
        prep_time_minutes=""
    )
    print("✅ Success: Empty strings for optional ints are accepted.")
    print(f"Parsed object: {obj}")
except Exception as e:
    print(f"❌ Failed: {e}")
