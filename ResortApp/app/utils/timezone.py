import pytz
from datetime import datetime
from cachetools import cached, TTLCache
from app.database import SessionLocal
from app.models.settings import SystemSetting

# Cache valid for 5 minutes
cache = TTLCache(maxsize=10, ttl=300)

@cached(cache)
def get_system_timezone_str() -> str:
    """Fetch the configured system timezone from DB; defaults to Asia/Kolkata if not setup."""
    db = SessionLocal()
    try:
        # Get the global setting for timezone (where key is "timezone", potentially branch_id=None or the first matched)
        setting = db.query(SystemSetting).filter(SystemSetting.key == "timezone").first()
        if setting and setting.value:
            return setting.value
        return 'Asia/Kolkata'
    except Exception as e:
        print(f"Warning: Failed to fetch system timezone from settings: {e}")
        return 'Asia/Kolkata'
    finally:
        db.close()

def get_system_timezone():
    """Returns the pytz timezone object based on system settings."""
    tz_str = get_system_timezone_str()
    try:
        return pytz.timezone(tz_str)
    except pytz.UnknownTimeZoneError:
        print(f"Warning: Unknown timezone {tz_str}, falling back to Asia/Kolkata.")
        return pytz.timezone('Asia/Kolkata')

def get_local_now() -> datetime:
    """Returns the current aware datetime in the configured system timezone."""
    return datetime.now(get_system_timezone())
