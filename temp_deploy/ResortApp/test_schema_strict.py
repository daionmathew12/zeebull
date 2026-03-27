from app.schemas.recipe import RecipeCreate

print("Testing Strict RecipeCreate schema validation...")
try:
    # Test with empty string for cook_time_minutes - SHOULD FAIL
    obj = RecipeCreate(
        food_item_id=1, 
        name="Test Recipe", 
        cook_time_minutes="",
        prep_time_minutes=""
    )
    print("❌ Failed: Should have rejected empty string but accepted it.")
except Exception as e:
    print(f"✅ Success: Rejected empty string as expected. Error: {e}")
