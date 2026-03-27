from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.user import Role
from app.schemas.user import RoleCreate
import json

def create_role(db: Session, role: RoleCreate, branch_id: int = None):
    # Check for existing role with same name in same branch
    query = db.query(Role).filter(func.lower(Role.name) == role.name.lower())
    if branch_id is not None:
        query = query.filter(Role.branch_id == branch_id)
    else:
        query = query.filter(Role.branch_id == None)
        
    existing_role = query.first()
    
    if existing_role:
        msg = f"Role with this name already exists {'in this branch' if branch_id else 'at enterprise level'}"
        raise HTTPException(status_code=400, detail=msg)
        
    # Store permissions as JSON string
    permissions_str = role.permissions if role.permissions else json.dumps([])
    db_role = Role(name=role.name, permissions=permissions_str, branch_id=branch_id)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(db: Session, role_id: int, role_data: RoleCreate, branch_id: int = None):
    query = db.query(Role).filter(Role.id == role_id)
    if branch_id is not None:
        query = query.filter(Role.branch_id == branch_id)
    db_role = query.first()
    
    if not db_role:
        return None
        
    # If name is being changed, check for duplicates
    if db_role.name.lower() != role_data.name.lower():
        query = db.query(Role).filter(func.lower(Role.name) == role_data.name.lower())
        if db_role.branch_id is not None:
            query = query.filter(Role.branch_id == db_role.branch_id)
        else:
            query = query.filter(Role.branch_id == None)
            
        existing_role = query.first()
        
        if existing_role:
            raise HTTPException(status_code=400, detail="Role with this name already exists")
    
    db_role.name = role_data.name
    # Store permissions as JSON string
    if role_data.permissions:
        db_role.permissions = role_data.permissions
    else:
        db_role.permissions = json.dumps([])
        
    db.commit()
    db.refresh(db_role)
    return db_role

def get_roles(db: Session, skip: int = 0, limit: int = 100, branch_id: int = None):
    query = db.query(Role)
    if branch_id is not None:
        query = query.filter(Role.branch_id == branch_id)
    return query.offset(skip).limit(limit).all()

def delete_role(db: Session, role_id: int, branch_id: int = None):
    query = db.query(Role).filter(Role.id == role_id)
    if branch_id is not None:
        query = query.filter(Role.branch_id == branch_id)
    db_role = query.first()
    
    if db_role:
        db.delete(db_role)
        db.commit()
        return True
    return False