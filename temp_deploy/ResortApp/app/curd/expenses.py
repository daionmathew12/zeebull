from sqlalchemy.orm import Session
from app.models.expense import Expense
from app.schemas.expenses import ExpenseCreate, ExpenseUpdate

def create_expense(db: Session, data, branch_id: int, image_path: str = None):

    # Handle both dict and Pydantic model
    if isinstance(data, dict):
        expense_data = ExpenseCreate(**data)
    else:
        expense_data = data
    
    # Create expense model
    new_expense = Expense(
        category=expense_data.category,
        amount=expense_data.amount,
        date=expense_data.date,
        description=expense_data.description,
        employee_id=expense_data.employee_id,
        image=image_path,
        department=getattr(expense_data, 'department', None),
        status=getattr(expense_data, 'status', 'Pending'),
        # RCM fields
        rcm_applicable=getattr(expense_data, 'rcm_applicable', False),
        rcm_tax_rate=getattr(expense_data, 'rcm_tax_rate', None),
        nature_of_supply=getattr(expense_data, 'nature_of_supply', None),
        original_bill_no=getattr(expense_data, 'original_bill_no', None),
        vendor_id=getattr(expense_data, 'vendor_id', None),
        rcm_liability_date=getattr(expense_data, 'rcm_liability_date', None),
        itc_eligible=getattr(expense_data, 'itc_eligible', True),
        branch_id=branch_id
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

def get_all_expenses(db: Session, branch_id: int, skip: int = 0, limit: int = 100):
    return db.query(Expense).filter(Expense.branch_id == branch_id).offset(skip).limit(limit).all()


def get_expense_by_id(db: Session, expense_id: int, branch_id: int):
    return db.query(Expense).filter(Expense.id == expense_id, Expense.branch_id == branch_id).first()


def update_expense(db: Session, expense_id: int, data: ExpenseUpdate, branch_id: int):
    expense = get_expense_by_id(db, expense_id, branch_id=branch_id)

    for field, value in data.dict(exclude_unset=True).items():
        setattr(expense, field, value)
    db.commit()
    return expense

def delete_expense(db: Session, expense_id: int, branch_id: int):
    expense = get_expense_by_id(db, expense_id, branch_id=branch_id)

    db.delete(expense)
    db.commit()
