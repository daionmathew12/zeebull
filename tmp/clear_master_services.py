import os
import sys

# Add the project root to sys.path
sys.path.append('/var/www/zeebull/ResortApp')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ResortApp')))

from app.database import SessionLocal, engine
from sqlalchemy import text

def clear_master_services():
    print("========================================")
    print("STAGING: Master Service Removal Tool")
    print("========================================")
    
    if sys.stdin.isatty():
        confirm = input("Are you absolutely sure you want to PERMANENTLY DELETE all service definitions? (y/N): ")
        if confirm.lower() != 'y':
            print("Cleanup aborted.")
            return
    else:
        print("Non-interactive mode: assuming 'y' from stdin.")

    tables = [
        "service_inventory_items",
        "service_images",
        "services"
    ]

    print("Cleaning up tables...")
    for table in tables:
        db = SessionLocal()
        try:
            db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
            db.commit()
            print(f" - Truncated: {table}")
        except Exception as e:
            db.rollback()
            print(f" - Skip: {table} (Error: {str(e).splitlines()[0]})")
        finally:
            db.close()

    print("\n========================================")
    print("SUCCESS: Master service catalog has been wiped.")
    print("========================================")

if __name__ == "__main__":
    clear_master_services()
