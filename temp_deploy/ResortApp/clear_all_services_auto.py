"""
Script to clear all assigned services and all services from the database (non-interactive).
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
    print(f"Loaded .env from: {env_path.absolute()}")
else:
    print(f"Warning: .env file not found at {env_path.absolute()}")

load_dotenv(override=True)

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Convert postgresql:// to postgresql+psycopg2:// if needed
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    print(f"Converted DATABASE_URL to use psycopg2 driver")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)
conn = engine.connect()

try:
    # Start transaction
    trans = conn.begin()
    
    print("\n1. Counting current records...")
    
    # Count assigned services
    result = conn.execute(text("SELECT COUNT(*) FROM assigned_services"))
    assigned_count = result.scalar()
    print(f"   Assigned Services: {assigned_count}")
    
    # Count services
    result = conn.execute(text("SELECT COUNT(*) FROM services"))
    services_count = result.scalar()
    print(f"   Services: {services_count}")
    
    # Count service images
    result = conn.execute(text("SELECT COUNT(*) FROM service_images"))
    images_count = result.scalar()
    print(f"   Service Images: {images_count}")
    
    # Count service inventory items
    result = conn.execute(text("SELECT COUNT(*) FROM service_inventory_items"))
    inventory_count = result.scalar()
    print(f"   Service Inventory Items: {inventory_count}")
    
    print(f"\n⚠️  Deleting all records...")
    
    print("\n2. Deleting assigned services...")
    result = conn.execute(text("DELETE FROM assigned_services"))
    deleted_assigned = result.rowcount
    print(f"   ✓ Deleted {deleted_assigned} assigned services")
    
    print("\n3. Deleting service inventory item links...")
    result = conn.execute(text("DELETE FROM service_inventory_items"))
    deleted_inventory = result.rowcount
    print(f"   ✓ Deleted {deleted_inventory} service inventory item links")
    
    print("\n4. Deleting service images...")
    result = conn.execute(text("DELETE FROM service_images"))
    deleted_images = result.rowcount
    print(f"   ✓ Deleted {deleted_images} service images")
    
    print("\n5. Deleting services...")
    result = conn.execute(text("DELETE FROM services"))
    deleted_services = result.rowcount
    print(f"   ✓ Deleted {deleted_services} services")
    
    # Commit transaction
    trans.commit()
    
    print("\n✅ Successfully cleared all services and assigned services!")
    print(f"\nSummary:")
    print(f"   - Deleted {deleted_assigned} assigned services")
    print(f"   - Deleted {deleted_services} services")
    print(f"   - Deleted {deleted_images} service images")
    print(f"   - Deleted {deleted_inventory} service inventory item links")
    
except Exception as e:
    trans.rollback()
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    conn.close()



