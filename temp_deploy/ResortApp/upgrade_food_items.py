from app.database import engine
from sqlalchemy import text

def upgrade_food_items():
    cols = [
        ("available_from_time", "VARCHAR"),
        ("available_to_time", "VARCHAR"),
        ("always_available", "BOOLEAN DEFAULT TRUE"),
        ("time_wise_prices", "TEXT"),
        ("room_service_price", "INTEGER DEFAULT 0"),
        ("extra_inventory_items", "TEXT")
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in cols:
            try:
                # Use quotes for column names if needed, but these are simple
                conn.execute(text(f"ALTER TABLE food_items ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Added {col_name}")
            except Exception as e:
                print(f"Note for {col_name}: {e}")

if __name__ == "__main__":
    upgrade_food_items()
