from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.utils.auth import get_current_user
from app.schemas.notification import NotificationOut, NotificationCreate
from app.curd import notification as notification_crud

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[NotificationOut])
def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all notifications"""
    return notification_crud.get_notifications(
        db, 
        skip=skip, 
        limit=limit, 
        unread_only=unread_only,
        user_id=current_user.id
    )

@router.get("", response_model=List[NotificationOut])  # Handle without trailing slash
def get_notifications_no_slash(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all notifications (no trailing slash)"""
    return notification_crud.get_notifications(
        db, 
        skip=skip, 
        limit=limit, 
        unread_only=unread_only,
        user_id=current_user.id
    )

@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    count = notification_crud.get_unread_count(db, user_id=current_user.id)
    return {"count": count}

@router.get("/{notification_id}", response_model=NotificationOut)
def get_notification(notification_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get a specific notification"""
    notification = notification_crud.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.post("/", response_model=NotificationOut)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new notification (admin only)"""
    return notification_crud.create_notification(db, notification)

@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(notification_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    notification = notification_crud.mark_notification_as_read(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.put("/mark-all-read")
def mark_all_as_read(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    count = notification_crud.mark_all_as_read(db)
    return {"message": f"Marked {count} notifications as read"}

@router.delete("/clear-all")
def clear_all_notifications(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Delete all notifications"""
    count = notification_crud.clear_all_notifications(db)
    return {"message": f"Deleted {count} notifications"}

@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Delete a specific notification"""
    success = notification_crud.delete_notification(db, notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted successfully"}
