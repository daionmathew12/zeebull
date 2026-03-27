import sys
import os

# Set up paths to match the app environment
sys.path.append("/var/www/zeebull/ResortApp")
os.chdir("/var/www/zeebull/ResortApp")

from app.database import SessionLocal
from app.models.Package import PackageBooking
from sqlalchemy import func

db = SessionLocal()
try:
    print("Testing query to package_bookings...")
    count = db.query(func.count(PackageBooking.id)).scalar()
    print(f"Success! Count: {count}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
