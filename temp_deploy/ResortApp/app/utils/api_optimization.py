"""
API Optimization Utilities for Low Network Performance
"""
from typing import Optional, Callable
from functools import wraps
from fastapi import Query, Response
from fastapi.responses import JSONResponse

# Standard limits for low network optimization
MAX_LIMIT_LOW_NETWORK = 50
DEFAULT_LIMIT = 20
MAX_LIMIT_STANDARD = 100

def optimize_limit(limit: int, max_limit: int = MAX_LIMIT_LOW_NETWORK) -> int:
    """
    Optimize limit parameter for low network conditions
    """
    if limit > max_limit:
        return max_limit
    if limit < 1:
        return DEFAULT_LIMIT
    return limit

def get_optimized_query_params(
    skip: int = 0,
    limit: int = DEFAULT_LIMIT,
    max_limit: int = MAX_LIMIT_LOW_NETWORK
) -> tuple[int, int]:
    """
    Get optimized skip and limit parameters
    Returns: (skip, optimized_limit)
    """
    optimized_limit = optimize_limit(limit, max_limit)
    return (skip, optimized_limit)

# Field selection helper (for future use)
def parse_fields(fields: Optional[str]) -> Optional[list]:
    """
    Parse comma-separated field list
    Example: "id,name,email" -> ["id", "name", "email"]
    """
    if not fields:
        return None
    return [f.strip() for f in fields.split(",") if f.strip()]


def apply_api_optimizations(func: Callable) -> Callable:
    """
    Decorator to apply API optimizations:
    - Caps limit parameters (handled by Query defaults)
    - Note: Caching headers are handled by FastAPI middleware
    - This is a pass-through decorator for consistency
    """
    # For now, just return the function as-is
    # The limit capping is already handled by Query parameter defaults
    # and caching is handled by middleware
    return func

