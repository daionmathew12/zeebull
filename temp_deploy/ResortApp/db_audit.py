import os
from sqlalchemy import create_engine, text

def audit():
    url = "postgresql+psycopg2://orchid_user:admin123@localhost/orchid_resort"
    print(f"Connecting to: {url}")
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            # Check Employees
            emp_count = conn.execute(text("SELECT count(*) FROM employees")).scalar()
            print(f"Employees: {emp_count}")
            
            # Check Users
            user_count = conn.execute(text("SELECT count(*) FROM users")).scalar()
            print(f"Users: {user_count}")
            
            # Check Payments
            has_payments = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'salary_payments')")).scalar()
            if has_payments:
                pay_count = conn.execute(text("SELECT count(*) FROM salary_payments")).scalar()
                print(f"Salary Payments: {pay_count}")
            else:
                print("Salary Payments: Table does not exist")
                
            # Check Rooms
            room_count = conn.execute(text("SELECT count(*) FROM rooms")).scalar()
            print(f"Rooms: {room_count}")
            
            # Check Inventory Items
            item_count = conn.execute(text("SELECT count(*) FROM inventory_items")).scalar()
            print(f"Inventory Items: {item_count}")
            
            # Check Categories
            cat_count = conn.execute(text("SELECT count(*) FROM inventory_categories")).scalar()
            print(f"Inventory Categories: {cat_count}")
                
            # Sample Employee 4
            emp_4 = conn.execute(text("SELECT id, name, user_id FROM employees WHERE id = 4")).fetchone()
            if emp_4:
                print(f"Employee 4: Found (ID={emp_4[0]}, Name={emp_4[1]}, UserID={emp_4[2]})")
            else:
                print("Employee 4: Not found")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit()
