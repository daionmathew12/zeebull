from app.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Adding created_by_id column...")
        try:
            conn.execute(text("ALTER TABLE food_orders ADD COLUMN created_by_id INTEGER REFERENCES employees(id)"))
            conn.commit()
            print("Successfully added created_by_id.")
        except Exception as e:
            print(f"Error adding created_by_id: {e}")

        print("Adding prepared_by_id column...")
        try:
            conn.execute(text("ALTER TABLE food_orders ADD COLUMN prepared_by_id INTEGER REFERENCES employees(id)"))
            conn.commit()
            print("Successfully added prepared_by_id.")
        except Exception as e:
            print(f"Error adding prepared_by_id: {e}")

if __name__ == "__main__":
    migrate()
