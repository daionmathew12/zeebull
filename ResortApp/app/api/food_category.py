from fastapi import APIRouter, Depends, UploadFile, File, Form
import os
# Absolute project root path (ResortApp/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_UPLOAD_ROOT = os.path.join(_BASE_DIR, "uploads")
from sqlalchemy.orm import Session
from app.schemas.food_category import *
from app.curd import food_category as crud
from app.utils.auth import get_db, get_current_user
from app.utils.branch_scope import get_branch_id
from app.models.food_category import FoodCategory
from app.models.user import User
import os, shutil, uuid

UPLOAD_DIR = os.path.join(_UPLOAD_ROOT, "food_categories")
os.makedirs(UPLOAD_DIR, exist_ok=True)
router = APIRouter(prefix="/food-categories", tags=["Food Categories"])


@router.post("", response_model=FoodCategoryOut)
def create_category(name: str = Form(...), image: UploadFile = File(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    filename = None
    if image:
        filename = f"category_{uuid.uuid4().hex}_{image.filename}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    
    category = FoodCategory(name=name, image=filename, branch_id=branch_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def _read_all_impl(db: Session, skip: int = 0, limit: int = 20, branch_id: int = None):
    """Helper function for read_all"""
    return crud.get_categories(db, skip=skip, limit=limit, branch_id=branch_id)

@router.get("", response_model=list[FoodCategoryOut])
def read_all(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id), skip: int = 0, limit: int = 20):
    return _read_all_impl(db, skip, limit, branch_id=branch_id)

@router.get("/", response_model=list[FoodCategoryOut])  # Handle trailing slash
def read_all_slash(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id), skip: int = 0, limit: int = 20):
    return _read_all_impl(db, skip, limit, branch_id=branch_id)

@router.put("/{cat_id}", response_model=FoodCategoryOut)
def update(cat_id: int, name: str = Form(...), image: UploadFile = File(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    """Update a food category"""
    category = db.query(FoodCategory).filter(FoodCategory.id == cat_id, FoodCategory.branch_id == branch_id).first()
    if not category:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Category not found")
    
    category.name = name
    
    # Handle image update if provided
    if image and image.filename:
        # Delete old image if exists
        if category.image:
            old_path = os.path.join(UPLOAD_DIR, category.image)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Save new image
        filename = f"category_{uuid.uuid4().hex}_{image.filename}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        category.image = filename
    
    db.commit()
    db.refresh(category)
    return category

@router.delete("/{cat_id}")
def delete(cat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    """Delete a food category"""
    category = db.query(FoodCategory).filter(FoodCategory.id == cat_id, FoodCategory.branch_id == branch_id).first()
    if not category:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Delete image if exists
    if category.image:
        image_path = os.path.join(UPLOAD_DIR, category.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}
