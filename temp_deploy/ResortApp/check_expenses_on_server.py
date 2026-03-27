from app.database import SessionLocal
from sqlalchemy import text
from app.models.expense import Expense
from app.models.employee import Employee
from app.models.inventory import Vendor

def check_expenses():
    db = SessionLocal()
    try:
        print("Checking expenses table...")
        count = db.query(Expense).count()
        print(f"Total expenses: {count}")
        
        # Check first few
        expenses = db.query(Expense).limit(5).all()
        for e in expenses:
            print(f"Expense ID: {e.id}, Category: {e.category}, Amount: {e.amount}, EmployeeID: {e.employee_id}, VendorID: {e.vendor_id}")
            # Try to get employee
            emp = db.query(Employee).filter(Employee.id == e.employee_id).first()
            print(f"  Employee Name: {emp.name if emp else 'NOT FOUND'}")
            # Try to get vendor
            if e.vendor_id:
                vendor = db.query(Vendor).filter(Vendor.id == e.vendor_id).first()
                print(f"  Vendor Name: {vendor.name if vendor else 'NOT FOUND'}")
        
        # Test the exact logic from the API
        print("\nTesting API logic...")
        skip = 0
        limit = 20
        expenses = db.query(Expense).offset(skip).limit(limit).all()
        result = []
        for exp in expenses:
            emp = db.query(Employee).filter(Employee.id == exp.employee_id).first()
            item = {
                "id": exp.id,
                "category": exp.category,
                "employee_name": emp.name if emp else "N/A"
            }
            result.append(item)
            print(f"Processed expense {exp.id}")
        print(f"Successfully processed {len(result)} expenses")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_expenses()
