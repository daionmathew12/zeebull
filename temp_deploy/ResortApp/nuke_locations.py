
import sys
import os
sys.path.append(os.getcwd())
sys.path.append('/var/www/inventory/ResortApp')

from app.database import SessionLocal
from sqlalchemy import text

def debug_location_and_nuke():
    db = SessionLocal()
    try:
        print("Checking Locations count...")
        t = "locations"
        try:
            count = db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            print(f"Table '{t}': {count} rows")
        except Exception as e:
            print(f"Table '{t}' check failed: {e}")
        
        print("\nPerforming TARGETED NUKE on Locations...")

        # Locations might be linked to operational data (issue logs etc) which we already cleared.
        # But they often link to themselves (parent_location_id).
        
        target = "locations"
        try:
            db.execute(text(f"TRUNCATE TABLE {target} CASCADE"))
            db.commit()
            print(f"✓ Truncated {target} SUCCESSFULLY")
        except Exception as e:
            print(f"❌ Failed to truncate {target}: {e}")
            db.rollback()

        print("\nFinal Check:")
        try:
            count = db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            print(f"Table '{t}': {count} rows")
        except: pass
            
    except Exception as e:
        print(f"Global Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_location_and_nuke()
