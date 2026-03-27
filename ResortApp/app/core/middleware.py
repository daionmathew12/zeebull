from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.database import SessionLocal
from app.models.activity_log import ActivityLog
from jose import jwt
import os
import time
import json

class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # We try to capture the request body for POST/PUT/DELETE
        # Note: Reading body here requires caution as it can hang if not handled, 
        # and BaseHTTPMiddleware has limitations. We'll stick to basic info for now
        # to ensure stability, or use a safer approach if needed.
        
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Only log API calls
        if request.url.path.startswith("/api"):
            # Extract User info and Branch info from request state
            # request.state is populated by get_current_user dependency
            user_id = getattr(request.state, "user_id", None)
            
            # Use branch_id from state if available, else None
            branch_id = getattr(request.state, "branch_id", None)
            
            # If branch_id is "all", it should be logged as None (global activity)
            if branch_id == "all":
                branch_id = None
            
            if not user_id:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
                        ALGORITHM = os.getenv("ALGORITHM", "HS256")
                        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                        user_id = payload.get("user_id")
                        # If we manually decode, we might not have branch_id easily, 
                        # but we can try to guess or use the anchor
                    except:
                        pass
            
            self.log_activity(request, response, user_id, branch_id, process_time)
             
        return response

    def log_activity(self, request, response, user_id, branch_id, process_time):
        try:
            db = SessionLocal()
            
            # Create a more user-friendly action description
            path = request.url.path
            method = request.method
            
            # Simple mapping for better readability
            action_map = {
                "POST": "Created/Added",
                "GET": "Viewed/List",
                "PUT": "Updated/Modified",
                "PATCH": "Updated/Modified",
                "DELETE": "Removed/Deleted"
            }
            
            friendly_action = f"{action_map.get(method, method)} {path.split('/')[-1].replace('-', ' ').title()}"
            if "login" in path: friendly_action = "User Login Attempt"
            if "logout" in path: friendly_action = "User Logout"
            
            log = ActivityLog(
                user_id=int(user_id) if user_id else None,
                action=friendly_action,
                method=method,
                path=path,
                status_code=response.status_code,
                client_ip=request.client.host if request.client else "Unknown",
                details=json.dumps({
                    "process_time_ms": round(process_time * 1000, 2),
                    "user_agent": request.headers.get("user-agent"),
                    "query_params": str(request.query_params)
                }),
                branch_id=branch_id or 1
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Logging failed: {e}")
