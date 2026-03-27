import sys
import os

# Set up paths to match the app environment
sys.path.append("/var/www/zeebull/ResortApp")
os.chdir("/var/www/zeebull/ResortApp")

from app.database import engine, Base
import app.models # Load all models

print("Reconciling database schema...")
try:
    Base.metadata.create_all(bind=engine)
    print("✓ Schema reconciled successfully!")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
