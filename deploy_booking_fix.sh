#!/bin/bash
# Deployment script to fix booking amounts on production Orchid server

echo "=== Orchid Booking Amount Fix Deployment ==="
echo ""

# Navigate to Orchid project
cd /var/www/resort/orchid_production/ResortApp || exit 1

echo "1. Activating virtual environment..."
source venv/bin/activate

echo "2. Adding total_amount column to package_bookings table..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check and add total_amount column
    check_query = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='package_bookings' AND column_name='total_amount'
    """)
    result = db.execute(check_query).fetchone()
    
    if not result:
        alter_query = text("ALTER TABLE package_bookings ADD COLUMN total_amount FLOAT DEFAULT 0.0")
        db.execute(alter_query)
        db.commit()
        print("✓ Added total_amount column to package_bookings")
    else:
        print("✓ total_amount column already exists")
except Exception as e:
    print(f"✗ Error: {e}")
    db.rollback()
finally:
    db.close()
PYTHON_SCRIPT

echo ""
echo "3. Adding leave balance columns to employees table..."
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    columns_to_add = [
        ("paid_leave_balance", "INTEGER DEFAULT 12"),
        ("sick_leave_balance", "INTEGER DEFAULT 12"),
        ("long_leave_balance", "INTEGER DEFAULT 5"),
        ("wellness_leave_balance", "INTEGER DEFAULT 5")
    ]
    
    for col_name, col_type in columns_to_add:
        check_query = text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='employees' AND column_name='{col_name}'
        """)
        result = db.execute(check_query).fetchone()
        
        if not result:
            alter_query = text(f"ALTER TABLE employees ADD COLUMN {col_name} {col_type}")
            db.execute(alter_query)
            db.commit()
            print(f"✓ Added {col_name} column")
        else:
            print(f"✓ {col_name} already exists")
except Exception as e:
    print(f"✗ Error: {e}")
    db.rollback()
finally:
    db.close()
PYTHON_SCRIPT

echo ""
echo "4. Pulling latest code changes from repository..."
git stash
git pull origin main  # or your branch name

echo ""
echo "5. Restarting Orchid service..."
sudo systemctl restart orchid

echo ""
echo "6. Checking service status..."
sudo systemctl status orchid --no-pager -l

echo ""
echo "=== Deployment Complete ==="
echo "The following changes have been applied:"
echo "  ✓ Added total_amount column to package_bookings table"
echo "  ✓ Added leave balance columns to employees table"
echo "  ✓ Updated code with self-healing logic for booking amounts"
echo "  ✓ Added /auth/me endpoint"
echo "  ✓ Restarted Orchid service"
echo ""
echo "Please test the Flutter app to verify booking amounts are displaying correctly."
