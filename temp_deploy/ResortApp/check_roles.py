from sqlalchemy import create_engine, text

def check():
    url = "postgresql+psycopg2://orchid_user:admin123@localhost/orchid_resort"
    engine = create_engine(url)
    with engine.connect() as conn:
        print("--- Employees ---")
        emps = conn.execute(text("SELECT id, name, role, user_id FROM employees")).fetchall()
        for e in emps:
            print(f"ID: {e[0]}, Name: {e[1]}, Role: {e[2]}, UserID: {e[3]}")
            
        print("--- All Roles in roles table ---")
        roles = conn.execute(text("SELECT id, name FROM roles")).fetchall()
        for r in roles:
            print(f"ID: {r[0]}, Name: {r[1]}")

if __name__ == "__main__":
    check()
