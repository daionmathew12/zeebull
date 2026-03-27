
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.database import SessionLocal
from app.models.activity_log import ActivityLog
import time
import traceback

class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            # If exception propagates here (usually caught by exception handlers), log it?
            # Exception handlers usually return a response, so call_next returns response.
            # If unhandled, it bubbles up.
            raise e

        # Logic after response is generated
        try:
            process_time = time.time() - start_time
            
            method = request.method
            path = request.url.path
            
            # Skip high-volume static/health endpoints to avoid noise, 
            # UNLESS user wants *everything*. User said "activity log with who where when what and how".
            # I will skip strictly static assets to avoid DB bloating.
            if (path.startswith("/active_static") or 
                path.startswith("/uploads") or 
                path.startswith("/landing") or
                path.startswith("/user-static") or
                path.startswith("/admin-static") or 
                path == "/health" or
                path == "/favicon.ico"):
                return response

            status_code = response.status_code
            client_ip = request.client.host if request.client else "unknown"
            
            # Attempt to get user_id from request state (set by Auth middleware)
            # If your auth middleware sets request.state.user or similar
            user_id = None
            if hasattr(request, "state") and hasattr(request.state, "user_id"):
                user_id = request.state.user_id
            
            # Log to database
            # We use a new session to ensure thread safety
            db = SessionLocal()
            try:
                log_entry = ActivityLog(
                    action=f"{method} {path}",
                    method=method,
                    path=path,
                    status_code=status_code,
                    client_ip=client_ip,
                    user_id=user_id,
                    details=f"Duration: {process_time:.4f}s"
                )
                db.add(log_entry)
                db.commit()
            except Exception as e:
                print(f"[ERROR] Failed to write activity log: {e}")
                # traceback.print_exc()
            finally:
                db.close()
                
        except Exception as log_error:
            print(f"[ERROR] Activity Logging Middleware Error: {log_error}")

        return response
