
import re

def patch_attendance():
    with open("remote_attendance.py", "r") as f:
        content = f.read()

    # 1. Add logging imports
    if "import logging" not in content:
        content = "import logging\nimport traceback\n" + content
        # Configure logging
        content = content.replace("router = APIRouter", 
                                  "logging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n\nrouter = APIRouter")

    # 2. Patch clock_in to be robust and temporarily public (optional: keep auth if confident, but let's debug)
    # We will keep auth but add try/except and logging
    
    # helper to find the function
    pattern = r'(@router\.post\("/clock-in".*?\)\s*\n\s*def clock_in\(.*?params.*?\):)(.*?)(\n@router)'
    # This regex is hard to match multi-lines perfectly.
    # Instead, we will replace the whole function text since we have the file content from view_file
    
    old_function = """@router.post("/clock-in", response_model=WorkingLogRecord)
def clock_in(clock_in_data: ClockInCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Use Indian Standard Time (IST)
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Check if there's an open clock-in for this employee today
    open_log = db.query(WorkingLog).filter(
        WorkingLog.employee_id == clock_in_data.employee_id,
        WorkingLog.date == now.date(),
        WorkingLog.check_out_time.is_(None)
    ).first()

    if open_log:
        raise HTTPException(status_code=400, detail="Employee is already clocked in. Please clock out first.")

    new_log = WorkingLog(
        employee_id=clock_in_data.employee_id,
        date=now.date(),
        check_in_time=now.time(),
        location=clock_in_data.location
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log"""

    new_function = """@router.post("/clock-in", response_model=WorkingLogRecord)
def clock_in(clock_in_data: ClockInCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        print(f"Clocking in request for {clock_in_data.employee_id}")
        # Use Indian Standard Time (IST)
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Check if there's an open clock-in for this employee today
        open_log = db.query(WorkingLog).filter(
            WorkingLog.employee_id == clock_in_data.employee_id,
            WorkingLog.date == now.date(),
            WorkingLog.check_out_time.is_(None)
        ).first()

        if open_log:
            raise HTTPException(status_code=400, detail="Employee is already clocked in. Please clock out first.")

        new_log = WorkingLog(
            employee_id=clock_in_data.employee_id,
            date=now.date(),
            check_in_time=now.time(),
            location=clock_in_data.location
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in clock_in: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))"""

    # We need to match exact string including indentation
    # The original file has indentation.
    # checking the view_file output... it uses 4 spaces.
    
    # Let's use simple string replace if it matches exactly
    # I will be careful with spaces.
    
    # Constructing exact old function string from lines 88-113 of view_file output
    old_func_exact = """@router.post("/clock-in", response_model=WorkingLogRecord)
def clock_in(clock_in_data: ClockInCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Use Indian Standard Time (IST)
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Check if there's an open clock-in for this employee today
    open_log = db.query(WorkingLog).filter(
        WorkingLog.employee_id == clock_in_data.employee_id,
        WorkingLog.date == now.date(),
        WorkingLog.check_out_time.is_(None)
    ).first()

    if open_log:
        raise HTTPException(status_code=400, detail="Employee is already clocked in. Please clock out first.")

    new_log = WorkingLog(
        employee_id=clock_in_data.employee_id,
        date=now.date(),
        check_in_time=now.time(),
        location=clock_in_data.location
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log"""

    if old_func_exact in content:
        content = content.replace(old_func_exact, new_function)
        print("Replaced clock_in function")
    else:
        # Fallback: simple text replacement line by line if needed or fail
        print("Could not match exact function text. Trying loose match.")
        
    with open("patched_attendance.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    patch_attendance()
