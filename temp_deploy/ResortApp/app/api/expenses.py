from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.curd import expenses as expense_crud
from app.utils.auth import get_db, get_current_user
from app.utils.branch_scope import get_branch_id

from app.schemas.expenses import ExpenseOut
from app.models.user import User
from app.models.employee import Employee
from app.utils.api_optimization import optimize_limit, MAX_LIMIT_LOW_NETWORK
import os
import shutil
from fastapi.responses import FileResponse
import uuid

router = APIRouter(prefix="/expenses", tags=["Expenses"])

UPLOAD_DIR = "uploads/expenses"


@router.post("", response_model=ExpenseOut)
async def create_expense(
    category: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    description: str = Form(None),
    employee_id: int = Form(...),
    department: str = Form(None),
    image: UploadFile = File(None),
    # RCM fields
    rcm_applicable: bool = Form(False),
    rcm_tax_rate: float = Form(None),
    nature_of_supply: str = Form(None),
    original_bill_no: str = Form(None),
    vendor_id: int = Form(None),
    rcm_liability_date: str = Form(None),
    itc_eligible: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id)
):

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    image_path = None
    if image and image.filename:
        filename = f"{employee_id}_{uuid.uuid4().hex}_{image.filename}"
        file_location = os.path.join(UPLOAD_DIR, filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Path to be used by frontend (relative to /uploads/)
        image_path = f"uploads/expenses/{filename}"

    # Store expense in DB using ExpenseCreate schema
    from app.schemas.expenses import ExpenseCreate
    from datetime import datetime
    from app.utils.accounting_helpers import generate_rcm_self_invoice_number, create_rcm_journal_entry
    from app.models.inventory import Vendor
    
    # Parse dates
    expense_date = datetime.strptime(date, "%Y-%m-%d").date() if isinstance(date, str) else date
    rcm_liability_dt = None
    if rcm_liability_date:
        rcm_liability_dt = datetime.strptime(rcm_liability_date, "%Y-%m-%d").date() if isinstance(rcm_liability_date, str) else rcm_liability_date
    
    # Generate self-invoice number if RCM is applicable
    self_invoice_number = None
    if rcm_applicable:
        self_invoice_number = generate_rcm_self_invoice_number(db)
    
    expense_data = ExpenseCreate(
        category=category,
        amount=amount,
        date=expense_date,
        description=description,
        employee_id=employee_id,
        department=department if department else None,
        rcm_applicable=rcm_applicable,
        rcm_tax_rate=rcm_tax_rate if rcm_applicable else None,
        nature_of_supply=nature_of_supply if rcm_applicable else None,
        original_bill_no=original_bill_no if rcm_applicable else None,
        vendor_id=vendor_id if vendor_id else None,
        rcm_liability_date=rcm_liability_dt if rcm_applicable else None,
        itc_eligible=itc_eligible if rcm_applicable else True
    )
    
    created = expense_crud.create_expense(db, data=expense_data, branch_id=branch_id, image_path=image_path)

    
    # Set self-invoice number if RCM is applicable
    if rcm_applicable and self_invoice_number:
        created.self_invoice_number = self_invoice_number
        db.commit()
        db.refresh(created)
    
    # Create RCM journal entry if applicable
    if rcm_applicable and rcm_tax_rate:
        try:
            # Get vendor details for journal entry
            vendor_name = "Unknown"
            is_interstate = False
            if vendor_id:
                vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()

                if vendor:
                    vendor_name = (vendor.legal_name or vendor.name) if vendor else "Unknown"
                    # Check if inter-state (compare vendor state with resort state)
                    if vendor.gst_number and len(vendor.gst_number) >= 2:
                        vendor_state_code = vendor.gst_number[:2]
                        from app.api.gst_reports import RESORT_STATE_CODE
                        is_interstate = vendor_state_code != RESORT_STATE_CODE
            
            # Create journal entry for RCM
            create_rcm_journal_entry(
                db=db,
                expense_id=created.id,
                taxable_value=float(amount),
                tax_rate=float(rcm_tax_rate),
                is_interstate=is_interstate,
                nature_of_supply=nature_of_supply or "Other",
                vendor_name=vendor_name,
                self_invoice_number=self_invoice_number,
                itc_eligible=itc_eligible,
                created_by=current_user.id,
                branch_id=branch_id
            )

        except Exception as e:
            # Log error but don't fail expense creation
            import traceback
            print(f"Warning: Could not create RCM journal entry for expense {created.id}: {str(e)}\n{traceback.format_exc()}")

            print(f"Warning: Could not create RCM journal entry for expense {created.id}: {str(e)}\n{traceback.format_exc()}")

    # Create Standard Expense Journal Entry (Debit Expense, Credit Cash/Bank)
    try:
        from app.utils.accounting_helpers import create_expense_journal_entry
        create_expense_journal_entry(
            db=db,
            expense_id=created.id,
            amount=float(amount),
            category=category,
            description=description or "",
            created_by=current_user.id,
            branch_id=branch_id
        )

    except Exception as je_error:
        print(f"Warning: Failed to create expense journal entry: {je_error}")

    # Add employee name in the response
    employee = db.query(Employee).filter(Employee.id == employee_id, Employee.branch_id == branch_id).first()

    return {
        **created.__dict__,
        "employee_name": employee.name if employee else "N/A"
    }

@router.get("", response_model=list[ExpenseOut])
def get_expenses(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
    branch_id: int = Depends(get_branch_id),
    skip: int = 0, 
    limit: int = 20
):

    # Cap limit to prevent performance issues
    # Optimized for low network
    limit = optimize_limit(limit, MAX_LIMIT_LOW_NETWORK)
    if limit < 1:
        limit = 20
    
    expenses = expense_crud.get_all_expenses(db, branch_id=branch_id, skip=skip, limit=limit)

    result = []
    for exp in expenses:
        emp = db.query(Employee).filter(Employee.id == exp.employee_id).first()
        result.append({
            **exp.__dict__,
            "employee_name": emp.name if emp else "N/A"
        })
    return result

@router.get("/image/{filename}")
def get_expense_image(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath)

@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id)
):
    expense = expense_crud.get_expense_by_id(db, expense_id, branch_id=branch_id)

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Delete associated image file if it exists
    if expense.image:
        image_path = expense.image
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                # Log error but continue with expense deletion
                print(f"Error deleting image file {image_path}: {e}")
    
    expense_crud.delete_expense(db, expense_id, branch_id=branch_id)

    return {"message": "Expense deleted successfully"}

@router.put("/{expense_id}/status/{status}")
def update_expense_status(
    expense_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    expense = expense_crud.get_expense_by_id(db, expense_id, branch_id=branch_id)

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    expense.status = status
    db.commit()
    return {"message": "Status updated"}


# Budget categories with default values
DEFAULT_BUDGETS = {
    "Utilities": 50000,
    "Maintenance": 75000,
    "Salary": 300000,
    "Food & Beverage": 100000,
    "Marketing": 40000,
    "Transportation": 30000,
    "Supplies": 60000,
    "Other": 50000
}

def _get_budgets_from_db(db: Session, branch_id: int) -> dict:
    """Read budget values from system_settings table for a branch, fall back to defaults."""
    from app.models.settings import SystemSetting
    budgets = dict(DEFAULT_BUDGETS)  # start with defaults
    for category in DEFAULT_BUDGETS:
        key = f"budget_{category.replace(' ', '_').replace('&', 'and')}"
        setting = db.query(SystemSetting).filter(SystemSetting.key == key, SystemSetting.branch_id == branch_id).first()

        if setting and setting.value:
            try:
                budgets[category] = float(setting.value)
            except ValueError:
                pass  # keep default
    return budgets


@router.get("/budgets")
def get_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """Get current budget settings for all expense categories in a branch."""
    budgets = _get_budgets_from_db(db, branch_id=branch_id)

    return {"budgets": [{"category": k, "amount": v} for k, v in budgets.items()]}


@router.post("/budgets")
def save_budgets(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):

    """
    Save budget amounts for expense categories.
    Payload: { "budgets": { "Utilities": 60000, "Salary": 350000, ... } }
    """
    from app.models.settings import SystemSetting
    budgets = payload.get("budgets", {})
    for category, amount in budgets.items():
        key = f"budget_{category.replace(' ', '_').replace('&', 'and')}"
        setting = db.query(SystemSetting).filter(SystemSetting.key == key, SystemSetting.branch_id == branch_id).first()

        if setting:
            setting.value = str(amount)
        else:
            setting = SystemSetting(
                key=key,
                value=str(amount),
                description=f"Monthly budget for {category}",
                branch_id=branch_id
            )
            db.add(setting)
    db.commit()

    return {"message": "Budget settings saved successfully"}


@router.get("/budget-analysis")
def get_budget_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):

    """
    Get budget vs actual spending analysis by category for current month.
    Budget amounts are read from system_settings (set via /expenses/budgets).
    """
    from datetime import datetime, date
    from sqlalchemy import func, extract
    from app.models.expense import Expense

    today = date.today()
    current_month = today.month
    current_year = today.year

    # Load budgets from DB (with defaults fallback)
    category_budgets = _get_budgets_from_db(db)

    # Get actual spending by category for current month
    actual_spending = db.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.branch_id == branch_id,
        extract('month', Expense.date) == current_month,
        extract('year', Expense.date) == current_year,
    ).group_by(Expense.category).all()


    actual_by_category = {item.category: float(item.total) for item in actual_spending}

    budget_data = []
    for category, budget in category_budgets.items():
        actual = actual_by_category.get(category, 0.0)
        variance = budget - actual
        percentage_used = (actual / budget * 100) if budget > 0 else 0
        budget_data.append({
            "category": category,
            "budget": budget,
            "actual": actual,
            "variance": variance,
            "percentage_used": round(percentage_used, 1),
            "status": "over_budget" if actual > budget else "within_budget"
        })

    # Include categories with spending but no budget defined
    for category, actual in actual_by_category.items():
        if category not in category_budgets:
            budget_data.append({
                "category": category,
                "budget": 0,
                "actual": actual,
                "variance": -actual,
                "percentage_used": 0,
                "status": "no_budget"
            })

    return {
        "month": today.strftime("%B %Y"),
        "categories": budget_data,
        "total_budget": sum(category_budgets.values()),
        "total_actual": sum(actual_by_category.values()),
        "total_variance": sum(category_budgets.values()) - sum(actual_by_category.values())
    }

