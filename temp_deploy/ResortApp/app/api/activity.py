from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.activity_log import ActivityLog
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/logs", description="Get activity logs")
def get_activity_logs(
    skip: int = 0, 
    limit: int = 100, 
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Require Admin?
):
    # Optional: Check if admin
    # if current_user.role != "admin": raise HTTPException...
    
    query = db.query(ActivityLog)
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
        
    logs = query.order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    # Simple serialization helper
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "user_id": log.user_id,
            "who": log.user.username if log.user else "Anonymous",
            "action": log.action,
            "details": log.details,
            "timestamp": log.timestamp,
            "ip": log.ip_address
        })
    return result
