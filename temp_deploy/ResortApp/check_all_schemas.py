from app.database import engine
from sqlalchemy import inspect

# Check all major tables for schema mismatches
tables_to_check = [
    ('bookings', 'app.models.booking', 'Booking'),
    ('rooms', 'app.models.room', 'Room'),
    ('inventory_items', 'app.models.inventory', 'InventoryItem'),
    ('food_orders', 'app.models.food_order', 'FoodOrder'),
    ('packages', 'app.models.Package', 'Package'),
    ('users', 'app.models.user', 'User'),
]

inspector = inspect(engine)

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
            print(f"\n{table_name}: Missing columns: {missing}")
        else:
            print(f"{table_name}: ✓ OK")
    except Exception as e:
        print(f"{table_name}: Error - {e}")
