import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

def migrate():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        print("Checking service_requests...")
        # billing_status
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='service_requests' AND column_name='billing_status'"))
        if not result.fetchone():
            print("Adding billing_status column to service_requests...")
            conn.execute(text("ALTER TABLE service_requests ADD COLUMN billing_status VARCHAR"))
            conn.commit()
            print("Successfully added billing_status column.")

        # started_at in service_requests
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='service_requests' AND column_name='started_at'"))
        if not result.fetchone():
            print("Adding started_at to service_requests...")
            conn.execute(text("ALTER TABLE service_requests ADD COLUMN started_at TIMESTAMP"))
            conn.commit()

        print("Checking package_bookings...")
        # created_at
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='package_bookings' AND column_name='created_at'"))
        if not result.fetchone():
            print("Adding created_at column to package_bookings...")
            conn.execute(text("ALTER TABLE package_bookings ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            conn.commit()
            print("Successfully added created_at column.")

        print("Checking packages...")
        # status
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='packages' AND column_name='status'"))
        if not result.fetchone():
            print("Adding status to packages...")
            conn.execute(text("ALTER TABLE packages ADD COLUMN status VARCHAR DEFAULT 'active'"))
            conn.commit()
        
        # created_at
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='packages' AND column_name='created_at'"))
        if not result.fetchone():
            print("Adding created_at column to packages...")
            conn.execute(text("ALTER TABLE packages ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            conn.commit()

        print("Checking assigned_services...")
        # started_at
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='assigned_services' AND column_name='started_at'"))
        if not result.fetchone():
            print("Adding started_at to assigned_services...")
            conn.execute(text("ALTER TABLE assigned_services ADD COLUMN started_at TIMESTAMP"))
            conn.commit()
        
        # completed_at
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='assigned_services' AND column_name='completed_at'"))
        if not result.fetchone():
            print("Adding completed_at to assigned_services...")
            conn.execute(text("ALTER TABLE assigned_services ADD COLUMN completed_at TIMESTAMP"))
            conn.commit()

        # override_charges
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='assigned_services' AND column_name='override_charges'"))
        if not result.fetchone():
            print("Adding override_charges to assigned_services...")
            conn.execute(text("ALTER TABLE assigned_services ADD COLUMN override_charges DOUBLE PRECISION"))
            conn.commit()

        print("Migration complete.")

if __name__ == "__main__":
    migrate()
