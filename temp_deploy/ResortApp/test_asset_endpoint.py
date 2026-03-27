import sys
sys.path.append('C:\\releasing\\New Orchid\\ResortApp')

from app.database import SessionLocal
from app.models.user import User
from app.api.inventory import get_asset_mappings

db = SessionLocal()

try:
    # Get a user for auth
    user = db.query(User).first()
    
    print("Testing get_asset_mappings...")
    result = get_asset_mappings(
        skip=0,
        limit=100,
        location_id=None,
        db=db,
        current_user=user
    )
    
    print(f"Success! Got {len(result)} mappings")
    for r in result[:3]:
        print(f"  - {r.get('item_name')} at {r.get('location_name')}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
