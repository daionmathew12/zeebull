"""
Recipe API endpoints for managing food item recipes with inventory items
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.utils.auth import get_db, get_current_user
from app.utils.branch_scope import get_branch_id
from app.models.user import User
from app.models.recipe import Recipe, RecipeIngredient
from app.models.food_item import FoodItem
from app.models.inventory import InventoryItem
from app.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeOut, RecipeIngredientOut

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.get("/test")
def test_recipe_router():
    """Test endpoint to verify router is loaded"""
    return {"message": "Recipe router is working!", "status": "ok"}


@router.post("", response_model=RecipeOut)
@router.post("/", response_model=RecipeOut)
def create_recipe(
    recipe: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """Create a new recipe for a food item"""
    try:
        # Verify food item exists
        food_item = db.query(FoodItem).filter(FoodItem.id == recipe.food_item_id, FoodItem.branch_id == branch_id).first()
        if not food_item:
            raise HTTPException(status_code=404, detail="Food item not found in this branch")
        
        # Create recipe
        db_recipe = Recipe(
            food_item_id=recipe.food_item_id,
            name=recipe.name,
            description=recipe.description,
            servings=recipe.servings,
            prep_time_minutes=recipe.prep_time_minutes,
            cook_time_minutes=recipe.cook_time_minutes,
            branch_id=branch_id
        )
        db.add(db_recipe)
        db.flush()  # Get recipe ID
        
        # Add ingredients
        total_cost = 0.0
        for ingredient_data in recipe.ingredients:
            # Verify inventory item exists
            inv_item = db.query(InventoryItem).filter(InventoryItem.id == ingredient_data.inventory_item_id, InventoryItem.branch_id == branch_id).first()
            if not inv_item:
                raise HTTPException(status_code=404, detail=f"Inventory item {ingredient_data.inventory_item_id} not found in this branch")
            
            db_ingredient = RecipeIngredient(
                recipe_id=db_recipe.id,
                inventory_item_id=ingredient_data.inventory_item_id,
                quantity=ingredient_data.quantity,
                unit=ingredient_data.unit,
                notes=ingredient_data.notes
            )
            db.add(db_ingredient)
            
            # Calculate cost (per serving)
            if inv_item.unit_price:
                cost_per_serving = (ingredient_data.quantity * inv_item.unit_price) / recipe.servings
                total_cost += cost_per_serving
        
        db.commit()
        db.refresh(db_recipe)
        
        # Load relationships for response
        db_recipe = db.query(Recipe).options(
            joinedload(Recipe.food_item),
            joinedload(Recipe.ingredients).joinedload(RecipeIngredient.inventory_item)
        ).filter(Recipe.id == db_recipe.id, Recipe.branch_id == branch_id).first()
        
        return _serialize_recipe(db_recipe, total_cost)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[ERROR] Error creating recipe: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create recipe: {str(e)}")


@router.get("", response_model=List[RecipeOut])
@router.get("/", response_model=List[RecipeOut])
def get_recipes(
    food_item_id: Optional[int] = Query(None, description="Filter by food item ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """Get all recipes, optionally filtered by food item"""
    try:
        query = db.query(Recipe).filter(Recipe.branch_id == branch_id).options(
            joinedload(Recipe.food_item),
            joinedload(Recipe.ingredients).joinedload(RecipeIngredient.inventory_item)
        )
        
        if food_item_id:
            query = query.filter(Recipe.food_item_id == food_item_id)
        
        recipes = query.order_by(Recipe.created_at.desc()).all()
        
        result = []
        for recipe in recipes:
            # Calculate total cost
            total_cost = 0.0
            for ingredient in recipe.ingredients:
                if ingredient.inventory_item and ingredient.inventory_item.unit_price:
                    cost_per_serving = (ingredient.quantity * ingredient.inventory_item.unit_price) / recipe.servings
                    total_cost += cost_per_serving
            
            result.append(_serialize_recipe(recipe, total_cost))
        
        return result
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error fetching recipes: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch recipes: {str(e)}")


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """Get a specific recipe by ID"""
    try:
        recipe = db.query(Recipe).options(
            joinedload(Recipe.food_item),
            joinedload(Recipe.ingredients).joinedload(RecipeIngredient.inventory_item)
        ).filter(Recipe.id == recipe_id, Recipe.branch_id == branch_id).first()
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Calculate total cost
        total_cost = 0.0
        for ingredient in recipe.ingredients:
            if ingredient.inventory_item and ingredient.inventory_item.unit_price:
                cost_per_serving = (ingredient.quantity * ingredient.inventory_item.unit_price) / recipe.servings
                total_cost += cost_per_serving
        
        return _serialize_recipe(recipe, total_cost)
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[ERROR] Error fetching recipe: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch recipe: {str(e)}")


@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """Update a recipe"""
    try:
        db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.branch_id == branch_id).first()
        if not db_recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Update basic fields
        if recipe_update.name is not None:
            db_recipe.name = recipe_update.name
        if recipe_update.description is not None:
            db_recipe.description = recipe_update.description
        if recipe_update.servings is not None:
            db_recipe.servings = recipe_update.servings
        if recipe_update.prep_time_minutes is not None:
            db_recipe.prep_time_minutes = recipe_update.prep_time_minutes
        if recipe_update.cook_time_minutes is not None:
            db_recipe.cook_time_minutes = recipe_update.cook_time_minutes
        
        # Update ingredients if provided
        if recipe_update.ingredients is not None:
            # Delete existing ingredients
            db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe_id).delete()
            
            # Add new ingredients
            total_cost = 0.0
            for ingredient_data in recipe_update.ingredients:
                inv_item = db.query(InventoryItem).filter(InventoryItem.id == ingredient_data.inventory_item_id, InventoryItem.branch_id == branch_id).first()
                if not inv_item:
                    raise HTTPException(status_code=404, detail=f"Inventory item {ingredient_data.inventory_item_id} not found in this branch")
                
                db_ingredient = RecipeIngredient(
                    recipe_id=recipe_id,
                    inventory_item_id=ingredient_data.inventory_item_id,
                    quantity=ingredient_data.quantity,
                    unit=ingredient_data.unit,
                    notes=ingredient_data.notes
                )
                db.add(db_ingredient)
                
                if inv_item.unit_price:
                    cost_per_serving = (ingredient_data.quantity * inv_item.unit_price) / db_recipe.servings
                    total_cost += cost_per_serving
        else:
            # Calculate cost from existing ingredients
            total_cost = 0.0
            for ingredient in db_recipe.ingredients:
                if ingredient.inventory_item and ingredient.inventory_item.unit_price:
                    cost_per_serving = (ingredient.quantity * ingredient.inventory_item.unit_price) / db_recipe.servings
                    total_cost += cost_per_serving
        
        db.commit()
        db.refresh(db_recipe)
        
        # Reload with relationships
        db_recipe = db.query(Recipe).options(
            joinedload(Recipe.food_item),
            joinedload(Recipe.ingredients).joinedload(RecipeIngredient.inventory_item)
        ).filter(Recipe.id == recipe_id, Recipe.branch_id == branch_id).first()
        
        return _serialize_recipe(db_recipe, total_cost)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[ERROR] Error updating recipe: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update recipe: {str(e)}")


@router.delete("/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """Delete a recipe"""
    try:
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id, Recipe.branch_id == branch_id).first()
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        db.delete(recipe)
        db.commit()
        
        return {"detail": "Recipe deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[ERROR] Error deleting recipe: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete recipe: {str(e)}")


def _serialize_recipe(recipe: Recipe, total_cost: float = None) -> dict:
    """Helper function to serialize recipe with all relationships"""
    ingredients = []
    calculated_cost = 0.0
    
    for ingredient in recipe.ingredients:
        if ingredient.inventory_item:
            ingredients.append(RecipeIngredientOut(
                id=ingredient.id,
                inventory_item_id=ingredient.inventory_item_id,
                inventory_item_name=ingredient.inventory_item.name,
                inventory_item_code=ingredient.inventory_item.item_code,
                quantity=ingredient.quantity,
                unit=ingredient.unit,
                notes=ingredient.notes
            ))
            
            if ingredient.inventory_item.unit_price and recipe.servings > 0:
                cost_per_serving = (ingredient.quantity * ingredient.inventory_item.unit_price) / recipe.servings
                calculated_cost += cost_per_serving
    
    return RecipeOut(
        id=recipe.id,
        food_item_id=recipe.food_item_id,
        food_item_name=recipe.food_item.name if recipe.food_item else None,
        name=recipe.name,
        description=recipe.description,
        servings=recipe.servings,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        ingredients=ingredients,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
        total_cost=total_cost if total_cost is not None else calculated_cost
    )

