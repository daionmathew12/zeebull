
from datetime import datetime, timezone, timedelta

def patch_attendance_no_pytz():
    with open("remote_attendance.py", "r") as f:
        content = f.read()

    # Imports
    if "from datetime import datetime, timedelta" not in content:
         # It likely has "from datetime import date, time, datetime, timedelta"
         pass
    
    # We will redefine the clock_in function to use built-in timezone
    
    old_func_part = 'def clock_in(clock_in_data: ClockInCreate'
    
    new_function = """@router.post("/clock-in", response_model=WorkingLogRecord)
def clock_in(clock_in_data: ClockInCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        print(f"Clocking in request for {clock_in_data.employee_id}")
        # Use Indian Standard Time (IST) manually without pytz
        # IST is UTC+5:30
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        # Check if there's an open clock-in for this employee today
        # Note: We compare date. now.date() returns local date in that timezone
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
        import traceback
        print(f"Error in clock_in: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))"""

    # We need to find the whole function block to replace it.
    # Since I don't have the exact previous file content state in memory perfectly (might have changed spacing),
    # I'll use regex to find the function start and end.
    
    import re
    # Match: @router.post... def clock_in... return new_log (end of function)
    # The previous patch might have been applied.
    
    # Let's try to match the signature
    pattern = r'@router\.post\("/clock-in".*?\)\s*def clock_in\(.*?\):'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # found start. assume function ends at next @router or end of file
        start_idx = match.start()
        
        # Find next router decorator
        next_router = re.search(r'@router\.(post|get|put|delete)', content[start_idx+1:])
        
        if next_router:
            end_idx = start_idx + 1 + next_router.start()
            # Replace the block
            new_content = content[:start_idx] + new_function + "\n\n" + content[end_idx:]
        else:
            # End of file
            new_content = content[:start_idx] + new_function
            
        with open("patched_attendance.py", "w") as f:
            f.write(new_content)
        print("Patched clock_in successfully")
    else:
        print("Could not find clock_in function to patch")

if __name__ == "__main__":
    patch_attendance_no_pytz()
