from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path

# Setup DB
env_path = Path('c:/releasing/New Orchid/ResortApp/.env')
load_dotenv(dotenv_path=env_path)
url = os.getenv("DATABASE_URL")
engine = create_engine(url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    from app.models.service import AssignedService, Service
    from app.models.inventory import InventoryItem, InventoryCategory
    
    # Test query
    print("Testing AssignedService query...")
    count = db.query(AssignedService).count()
    print(f"Count of AssignedService: {count}")
    
    # Test query with relationship
    print("Testing AssignedService with eager loads...")
    from sqlalchemy.orm import joinedload
    rows = db.query(AssignedService).options(
        joinedload(AssignedService.service),
        joinedload(AssignedService.employee),
        joinedload(AssignedService.room)
    ).limit(5).all()
    print(f"Loaded {len(rows)} records.")
    
    for row in rows:
        print(f"ID: {row.id}, Service: {row.service.name if row.service else 'None'}")
        # Test images access
        if row.service:
            print(f"  Images count: {len(row.service.images)}")
    
    db.close()
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
finally:
    db.close()
