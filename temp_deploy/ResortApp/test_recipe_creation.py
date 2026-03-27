from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from app.database import Base
from app.models.recipe import Recipe, RecipeIngredient
from app.models.food_item import FoodItem
from app.models.inventory import InventoryItem
import traceback

DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def test_recipe_creation():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    print("=== TESTING RECIPE CREATION ===")
    
    try:
        # Input data
        food_item_id = 1
        inventory_item_id = 1
        name = "Test Recipe"
        description = "Testing creation"
        servings = 10
        prep_time = 30
        cook_time = 0
        ingredients = [
            {"inventory_item_id": 1, "quantity": 1, "unit": "kg", "notes": "test"}
        ]
        
        # 1. Verify food item
        print(f"Querying FoodItem {food_item_id}...")
        food_item = db.query(FoodItem).filter(FoodItem.id == food_item_id).first()
        if not food_item:
            print("❌ Food item not found")
            return
        print(f"✅ Found FoodItem: {food_item.name}")
        
        # 2. Create recipe
        print("Creating Recipe object...")
        db_recipe = Recipe(
            food_item_id=food_item_id,
            name=name,
            description=description,
            servings=servings,
            prep_time_minutes=prep_time,
            cook_time_minutes=cook_time
        )
        db.add(db_recipe)
        print("Flushing recipe...")
        db.flush()
        print(f"✅ Recipe flushed, ID: {db_recipe.id}")
        
        # 3. Add ingredients
        total_cost = 0.0
        for ing in ingredients:
            print(f"Querying InventoryItem {ing['inventory_item_id']}...")
            inv_item = db.query(InventoryItem).filter(InventoryItem.id == ing['inventory_item_id']).first()
            if not inv_item:
                print("❌ Inventory item not found")
                return
            
            print("Creating RecipeIngredient...")
            db_ingredient = RecipeIngredient(
                recipe_id=db_recipe.id,
                inventory_item_id=ing['inventory_item_id'],
                quantity=ing['quantity'],
                unit=ing['unit'],
                notes=ing['notes']
            )
            db.add(db_ingredient)
            
            if inv_item.unit_price:
                cost = (ing['quantity'] * inv_item.unit_price) / servings
                total_cost += cost
                print(f"Calculated cost: {cost} (Unit Price: {inv_item.unit_price})")
        
        print("Committing transaction...")
        db.commit()
        print("✅ Transaction committed")
        
        print("Refreshing recipe...")
        db.refresh(db_recipe)
        
        print("Loading relationships...")
        # This is where serialization logic starts
        db_recipe = db.query(Recipe).options(
            joinedload(Recipe.food_item),
            joinedload(Recipe.ingredients).joinedload(RecipeIngredient.inventory_item)
        ).filter(Recipe.id == db_recipe.id).first()
        
        print(f"✅ Loaded relationships.")
        print(f"Food Item Name: {db_recipe.food_item.name}")
        for ing in db_recipe.ingredients:
             print(f"Ingredient: {ing.inventory_item.name}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ EXCEPTION CAUGHT: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_recipe_creation()
