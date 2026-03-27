from fastapi import Depends, HTTPException, Header, Request, status
from typing import Optional
from app.utils.auth import get_current_user
from app.models.user import User

def get_branch_id(
    request: Request,
    current_user: User = Depends(get_current_user),
    x_branch_id: Optional[str] = Header(None, alias="X-Branch-ID")
) -> Optional[int]:
    """
    Dependency to get the branch_id for scoping data.
    - If user is superadmin AND sends X-Branch-ID: all  → return None (all branches)
    - If user is superadmin AND sends X-Branch-ID: <num> → return that specific branch
    - If user is superadmin with no header             → use their own branch_id (or None if not set)
    - If user is NOT superadmin                        → always use their assigned branch_id
    """
    if getattr(current_user, "is_superadmin", False):
        if x_branch_id is not None:
            if x_branch_id.lower() == 'all':
                return None  # Enterprise view — show all branches
            try:
                return int(x_branch_id)
            except ValueError:
                pass
        # No header sent — fall back to the superadmin's own branch_id (may be None for true global admins)
        return getattr(current_user, 'branch_id', None)
    
    if current_user.branch_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to any branch."
        )
        
    return current_user.branch_id
