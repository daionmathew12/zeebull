import os
from sqlalchemy import create_engine, text

def audit():
    url = "postgresql+psycopg2://orchid_user:admin123@localhost/orchid_resort"
    engine = create_engine(url)
    with engine.connect() as conn:
        res = []
        res.append(f"Employees: {conn.execute(text('SELECT count(*) FROM employees')).scalar()}")
        res.append(f"Users: {conn.execute(text('SELECT count(*) FROM users')).scalar()}")
        
        has_pay = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'salary_payments')")).scalar()
        if has_pay:
            res.append(f"Payments: {conn.execute(text('SELECT count(*) FROM salary_payments')).scalar()}")
        else:
            res.append("Payments: Table Missing")
            
        res.append(f"Rooms: {conn.execute(text('SELECT count(*) FROM rooms')).scalar()}")
        res.append(f"Items: {conn.execute(text('SELECT count(*) FROM inventory_items')).scalar()}")
        res.append(f"Categories: {conn.execute(text('SELECT count(*) FROM inventory_categories')).scalar()}")
        
        print(" | ".join(res))

if __name__ == "__main__":
    audit()
