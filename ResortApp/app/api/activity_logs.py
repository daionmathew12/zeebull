from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.utils.auth import get_current_user
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])

@router.get("")
def get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    user_id: Optional[int] = None,
    hours: Optional[int] = Query(None, description="Filter logs from last N hours"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get activity logs with optional filters.
    """
    # Query ActivityLog and User (Joined)
    query = db.query(ActivityLog, User).outerjoin(User, ActivityLog.user_id == User.id)
    
    # Apply filters
    if method:
        query = query.filter(ActivityLog.method == method.upper())
    
    if path:
        query = query.filter(ActivityLog.path.contains(path))
    
    if status_code:
        query = query.filter(ActivityLog.status_code == status_code)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    if hours:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(ActivityLog.timestamp >= time_threshold)
    
    # Order by most recent first
    query = query.order_by(ActivityLog.timestamp.desc())
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    logs = query.offset(skip).limit(limit).all()
    
    # Convert to dict for JSON response
    results = []
    for log, user in logs:
            results.append({
            "id": log.id,
            "action": log.action,
            "method": log.method,
            "path": log.path,
            "status_code": log.status_code,
            "client_ip": log.client_ip,
            "user_id": log.user_id,
            "user_name": user.name if user else None,
            "user_email": user.email if user else None,
            "branch_id": log.branch_id,
            "details": log.details,
            "timestamp": log.timestamp.isoformat() + "Z" if log.timestamp else None
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "logs": results
    }

@router.get("/stats")
def get_activity_stats(
    hours: int = Query(24, description="Get stats from last N hours"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get activity statistics.
    """
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Total requests
    total_requests = db.query(ActivityLog).filter(
        ActivityLog.timestamp >= time_threshold
    ).count()
    
    # Success rate (2xx status codes)
    successful_requests = db.query(ActivityLog).filter(
        ActivityLog.timestamp >= time_threshold,
        ActivityLog.status_code >= 200,
        ActivityLog.status_code < 300
    ).count()
    
    # Error rate (4xx and 5xx)
    error_requests = db.query(ActivityLog).filter(
        ActivityLog.timestamp >= time_threshold,
        ActivityLog.status_code >= 400
    ).count()
    
    # Most common endpoints
    from sqlalchemy import func
    common_endpoints = db.query(
        ActivityLog.path,
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.timestamp >= time_threshold
    ).group_by(ActivityLog.path).order_by(func.count(ActivityLog.id).desc()).limit(10).all()
    
    # Most common status codes
    common_status_codes = db.query(
        ActivityLog.status_code,
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.timestamp >= time_threshold
    ).group_by(ActivityLog.status_code).order_by(func.count(ActivityLog.id).desc()).limit(10).all()
    
    return {
        "period_hours": hours,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "error_requests": error_requests,
        "success_rate": round((successful_requests / total_requests * 100) if total_requests > 0 else 0, 2),
        "error_rate": round((error_requests / total_requests * 100) if total_requests > 0 else 0, 2),
        "top_endpoints": [{"path": path, "count": count} for path, count in common_endpoints],
        "status_codes": [{"code": code, "count": count} for code, count in common_status_codes]
    }
