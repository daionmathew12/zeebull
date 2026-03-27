"""
Delete ALL entries from service-related tables.
This will permanently delete:
- All assigned services
- All service inventory item links
- All service images
- All services
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print("=" * 60)
print("DELETING ALL SERVICES AND ASSIGNED SERVICES")
print("=" * 60)

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    trans = conn.begin()
    try:
        # Count before deletion
        print("\n1. Counting current records...")
        result = conn.execute(text("SELECT COUNT(*) FROM assigned_services"))
        assigned_count = result.scalar()
        print(f"   Assigned Services: {assigned_count}")
        
        result = conn.execute(text("SELECT COUNT(*) FROM service_inventory_items"))
        inventory_count = result.scalar()
        print(f"   Service Inventory Items: {inventory_count}")
        
        result = conn.execute(text("SELECT COUNT(*) FROM service_images"))
        images_count = result.scalar()
        print(f"   Service Images: {images_count}")
        
        result = conn.execute(text("SELECT COUNT(*) FROM services"))
        services_count = result.scalar()
        print(f"   Services: {services_count}")
        
        # Delete in correct order
        print("\n2. Deleting all records...")
        
        print("   - Deleting assigned_services...")
        result = conn.execute(text("DELETE FROM assigned_services"))
        deleted_assigned = result.rowcount
        print(f"     ✓ Deleted {deleted_assigned} assigned services")
        
        print("   - Deleting service_inventory_items...")
        result = conn.execute(text("DELETE FROM service_inventory_items"))
        deleted_inventory = result.rowcount
        print(f"     ✓ Deleted {deleted_inventory} service inventory item links")
        
        print("   - Deleting service_images...")
        result = conn.execute(text("DELETE FROM service_images"))
        deleted_images = result.rowcount
        print(f"     ✓ Deleted {deleted_images} service images")
        
        print("   - Deleting services...")
        result = conn.execute(text("DELETE FROM services"))
        deleted_services = result.rowcount
        print(f"     ✓ Deleted {deleted_services} services")
        
        # Commit
        trans.commit()
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS: ALL SERVICES AND ASSIGNED SERVICES DELETED!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Deleted {deleted_assigned} assigned services")
        print(f"  - Deleted {deleted_services} services")
        print(f"  - Deleted {deleted_images} service images")
        print(f"  - Deleted {deleted_inventory} service inventory item links")
        print("\nAll tables are now empty.")
        
    except Exception as e:
        trans.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



