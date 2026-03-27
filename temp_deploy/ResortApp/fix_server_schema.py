#!/usr/bin/env python3
import sys
sys.path.insert(0, '/var/www/inventory/ResortApp')

from app.database import engine
from sqlalchemy import inspect, text

# Check all major tables for schema mismatches
tables_to_check = [
    ('bookings', 'app.models.booking', 'Booking'),
    ('rooms', 'app.models.room', 'Room'),
    ('inventory_items', 'app.models.inventory', 'InventoryItem'),
    ('packages', 'app.models.Package', 'Package'),
]

inspector = inspect(engine)
fixes_needed = []

for table_name, module_path, class_name in tables_to_check:
    try:
        # Import the model
        parts = module_path.rsplit('.', 1)
        mod = __import__(parts[0], fromlist=[parts[1]])
        model_class = getattr(getattr(mod, parts[1]), class_name)
        
        # Get columns
        db_columns = set([c['name'] for c in inspector.get_columns(table_name)])
        model_columns = set([c.name for c in model_class.__table__.columns])
        
        missing = model_columns - db_columns
        if missing:
            print(f"{table_name}: Missing columns: {missing}")
            for col_name in missing:
                col = model_class.__table__.columns[col_name]
                col_type = str(col.type)
                default = f"DEFAULT {col.default.arg}" if col.default else ""
                nullable = "NULL" if col.nullable else "NOT NULL"
                fixes_needed.append(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type} {default} {nullable};")
        else:
            print(f"{table_name}: ✓ OK")
    except Exception as e:
        print(f"{table_name}: Error - {e}")

if fixes_needed:
    print("\n--- SQL Fixes Needed ---")
    for fix in fixes_needed:
        print(fix)
    
    # Apply fixes
    with engine.connect() as conn:
        for fix in fixes_needed:
            try:
                conn.execute(text(fix))
                print(f"✓ Applied: {fix[:50]}...")
            except Exception as e:
                print(f"✗ Failed: {fix[:50]}... - {e}")
        conn.commit()
    print("\nAll fixes applied!")
else:
    print("\nNo fixes needed!")
