"""
Utility functions for parsing and handling booking display IDs.
Display IDs format: BK-000001 (regular booking) or PK-000001 (package booking)
"""
from typing import Tuple, Optional


def parse_display_id(display_id: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Parse a display ID (BK-000001, BK-1-000001, PK-000001, PK-1-000001) and return the numeric ID and type.
    
    Args:
        display_id: Display ID string (e.g., "BK-1-000001" or "BK-000001")
        
    Returns:
        Tuple of (numeric_id, booking_type) where:
        - numeric_id: The numeric part of the ID (e.g., 1)
        - booking_type: "booking" for BK- prefix, "package" for PK- prefix, None if invalid
    """
    if not display_id:
        return None, None
    
    # Check if it's a display ID format
    if "-" in display_id:
        parts = display_id.split("-")
        if len(parts) >= 2:
            prefix = parts[0].upper()
            # The numeric ID is always the last part
            numeric_part = parts[-1].lstrip("0") or "0"
            
            try:
                numeric_id = int(numeric_part)
                if prefix == "BK":
                    return numeric_id, "booking"
                elif prefix == "PK":
                    return numeric_id, "package"
            except ValueError:
                pass
    
    # If not in display ID format, try to parse as numeric ID
    try:
        numeric_id = int(display_id)
        return numeric_id, None
    except ValueError:
        return None, None


def format_display_id(numeric_id: int, branch_id: int = 1, is_package: bool = False) -> str:
    """
    Format a numeric ID into a display ID including branch ID.
    
    Args:
        numeric_id: The numeric ID
        branch_id: The branch ID
        is_package: True for package booking, False for regular booking
        
    Returns:
        Formatted display ID (e.g., "BK-1-000001" or "PK-1-000001")
    """
    prefix = "PK" if is_package else "BK"
    return f"{prefix}-{branch_id}-{str(numeric_id).zfill(6)}"


