from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def check_ice_cream():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Searching for 'Ice cream'...")
        result = conn.execute(text("SELECT id, name FROM food_items WHERE name ILIKE '%Ice cream%'")).fetchall()
        if result:
            for row in result:
                print(f"Found: {row[0]} - {row[1]}")
        else:
            print("❌ 'Ice cream' NOT FOUND in Postgres.")

if __name__ == "__main__":
    check_ice_cream()
