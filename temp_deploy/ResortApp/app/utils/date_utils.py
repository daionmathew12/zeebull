"""
Date and Time Utilities for India/Kerala (IST - UTC+5:30)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import pytz

# IST timezone constant
IST_TIMEZONE = pytz.timezone('Asia/Kolkata')

def get_ist_now() -> datetime:
    """
    Get current datetime in IST timezone
    
    Returns:
        datetime: Current datetime in IST
    """
    return datetime.now(IST_TIMEZONE)

def get_ist_today() -> datetime:
    """
    Get today's date at midnight in IST timezone
    
    Returns:
        datetime: Today at 00:00:00 IST
    """
    now_ist = get_ist_now()
    return now_ist.replace(hour=0, minute=0, second=0, microsecond=0)

def to_ist(dt: Union[datetime, str, None]) -> Optional[datetime]:
    """
    Convert a datetime to IST timezone
    
    Args:
        dt: datetime object, ISO string, or None
        
    Returns:
        datetime: Datetime in IST timezone, or None if input is None
    """
    if dt is None:
        return None
    
    # If string, parse it
    if isinstance(dt, str):
        try:
            # Try parsing ISO format
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            # Try other common formats
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                dt = datetime.strptime(dt, '%Y-%m-%d')
    
    # If datetime is naive (no timezone), assume it's already in IST
    if dt.tzinfo is None:
        return IST_TIMEZONE.localize(dt)
    
    # Convert to IST
    return dt.astimezone(IST_TIMEZONE)

def format_datetime_ist(dt: Union[datetime, str, None], format_str: str = '%d %b %Y, %I:%M %p') -> str:
    """
    Format datetime in IST timezone
    
    Args:
        dt: datetime object, ISO string, or None
        format_str: Format string (default: 'DD MMM YYYY, HH:MM AM/PM')
        
    Returns:
        str: Formatted datetime string, or '-' if None
    """
    if dt is None:
        return '-'
    
    dt_ist = to_ist(dt)
    if dt_ist is None:
        return '-'
    
    return dt_ist.strftime(format_str)

def format_date_ist(dt: Union[datetime, str, None], format_str: str = '%d %b %Y') -> str:
    """
    Format date in IST timezone
    
    Args:
        dt: datetime object, ISO string, or None
        format_str: Format string (default: 'DD MMM YYYY')
        
    Returns:
        str: Formatted date string, or '-' if None
    """
    if dt is None:
        return '-'
    
    dt_ist = to_ist(dt)
    if dt_ist is None:
        return '-'
    
    return dt_ist.strftime(format_str)

def format_time_ist(dt: Union[datetime, str, None], format_str: str = '%I:%M %p') -> str:
    """
    Format time in IST timezone
    
    Args:
        dt: datetime object, ISO string, or None
        format_str: Format string (default: 'HH:MM AM/PM')
        
    Returns:
        str: Formatted time string, or '-' if None
    """
    if dt is None:
        return '-'
    
    dt_ist = to_ist(dt)
    if dt_ist is None:
        return '-'
    
    return dt_ist.strftime(format_str)

def get_ist_date_range(period: str = 'today'):
    """
    Get date range in IST timezone
    
    Args:
        period: 'today', 'week', 'month', 'year'
        
    Returns:
        tuple: (start_date, end_date) as datetime objects in IST
    """
    today_ist = get_ist_today()
    
    if period == 'today':
        start_date = today_ist
        end_date = today_ist + timedelta(days=1)
    elif period == 'week':
        # Start of week (Monday)
        days_since_monday = today_ist.weekday()
        start_date = today_ist - timedelta(days=days_since_monday)
        end_date = start_date + timedelta(days=7)
    elif period == 'month':
        # Start of month
        start_date = today_ist.replace(day=1)
        # Start of next month
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
    elif period == 'year':
        # Start of year
        start_date = today_ist.replace(month=1, day=1)
        # Start of next year
        end_date = start_date.replace(year=start_date.year + 1)
    else:
        start_date = today_ist
        end_date = today_ist + timedelta(days=1)
    
    return start_date, end_date

def utc_to_ist(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST
    
    Args:
        utc_dt: UTC datetime object
        
    Returns:
        datetime: Datetime in IST
    """
    if utc_dt.tzinfo is None:
        # Assume UTC if naive
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    return utc_dt.astimezone(IST_TIMEZONE)

def ist_to_utc(ist_dt: datetime) -> datetime:
    """
    Convert IST datetime to UTC
    
    Args:
        ist_dt: IST datetime object
        
    Returns:
        datetime: Datetime in UTC
    """
    if ist_dt.tzinfo is None:
        # Assume IST if naive
        ist_dt = IST_TIMEZONE.localize(ist_dt)
    
    return ist_dt.astimezone(timezone.utc)








