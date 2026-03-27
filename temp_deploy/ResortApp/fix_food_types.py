from app.database import engine
from sqlalchemy import text

def fix_types():
    queries = [
        "ALTER TABLE food_items ALTER COLUMN price TYPE FLOAT",
        "ALTER TABLE food_items ALTER COLUMN room_service_price TYPE FLOAT",
        "ALTER TABLE food_items ALTER COLUMN available TYPE BOOLEAN USING (available::boolean)"
    ]
    
    with engine.connect() as conn:
        for q in queries:
            try:
                conn.execute(text(q))
                conn.commit()
                print(f"Executed: {q}")
            except Exception as e:
                print(f"Error executing {q}: {e}")

if __name__ == "__main__":
    fix_types()
