"""
Utility functions for parsing and handling booking display IDs.
Display IDs format: BK-000001 (regular booking) or PK-000001 (package booking)
"""
from typing import Tuple, Optional


def parse_display_id(display_id: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Parse a display ID (BK-000001 or PK-000001) and return the numeric ID and type.
    
    Args:
        display_id: Display ID string (e.g., "BK-000001" or "PK-000001")
        
    Returns:
        Tuple of (numeric_id, booking_type) where:
        - numeric_id: The numeric part of the ID (e.g., 1)
        - booking_type: "booking" for BK- prefix, "package" for PK- prefix, None if invalid
        
    Examples:
        parse_display_id("BK-000001") -> (1, "booking")
        parse_display_id("PK-000002") -> (2, "package")
        parse_display_id("123") -> (123, None)  # Treat as numeric ID
    """
    if not display_id:
        return None, None
    
    # Check if it's a display ID format (BK-000001 or PK-000001)
    if "-" in display_id:
        parts = display_id.split("-", 1)
        if len(parts) == 2:
            prefix = parts[0].upper()
            numeric_part = parts[1].lstrip("0") or "0"  # Remove leading zeros, but keep at least "0"
            
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


def format_display_id(numeric_id: int, is_package: bool = False) -> str:
    """
    Format a numeric ID into a display ID.
    
    Args:
        numeric_id: The numeric ID
        is_package: True for package booking, False for regular booking
        
    Returns:
        Formatted display ID (e.g., "BK-000001" or "PK-000001")
    """
    prefix = "PK" if is_package else "BK"
    return f"{prefix}-{str(numeric_id).zfill(6)}"


