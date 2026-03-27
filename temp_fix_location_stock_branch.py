import os
import sys

# Force UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.database import SessionLocal
from app.models.inventory import LocationStock, Location, PurchaseMaster

def fix_location_stock_branch():
    db = SessionLocal()
    try:
        # Find all location stocks where branch_id is None
        # We can also just update them all correctly based on the 'Location' they belong to,
        # which is the most accurate fallback!
        stocks = db.query(LocationStock).all()
        updated_count = 0
        for stock in stocks:
            if getattr(stock, 'branch_id', None) is None:
                loc = db.query(Location).filter(Location.id == stock.location_id).first()
                if loc and loc.branch_id:
                    stock.branch_id = loc.branch_id
                    updated_count += 1
                else:
                    stock.branch_id = 1 # Fallback
                    updated_count += 1
        if updated_count > 0:
            db.commit()
        print(f"Fixed {updated_count} LocationStock records with missing branch_id.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_location_stock_branch()
