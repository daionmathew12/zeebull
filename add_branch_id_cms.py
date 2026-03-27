import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))
from sqlalchemy import text
from app.database import SessionLocal

def add_branch_id():
    db = SessionLocal()
    try:
        tables = ['header_banner', 'gallery', 'reviews', 'signature_experiences', 'plan_weddings', 'nearby_attractions', 'nearby_attraction_banners']
        for table in tables:
            print(f"Adding branch_id to {table}...")
            # Using raw SQL to add column
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS branch_id INTEGER"))
            # Add foreign key constraint
            db.execute(text(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_{table}_branch') THEN ALTER TABLE {table} ADD CONSTRAINT fk_{table}_branch FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL; END IF; END $$;"))
            db.commit()
            print(f"Success for {table}")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_branch_id()
