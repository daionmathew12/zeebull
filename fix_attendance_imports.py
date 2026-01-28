
import re

def fix_imports():
    with open("patched_attendance.py", "r") as f:
        content = f.read()
        
    # Replace "from datetime import date, time, datetime, timedelta" 
    # with "from datetime import date, time, datetime, timedelta, timezone"
    
    old_import = "from datetime import date, time, datetime, timedelta"
    new_import = "from datetime import date, time, datetime, timedelta, timezone"
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        print("Fixed imports")
    else:
        # Maybe it already has it or different formatting
        print("Could not find exact import string to replace. Checking if timezone is already there.")
        if ", timezone" not in content and "import timezone" not in content:
             # Try regex
             content = re.sub(r'from datetime import ([\w,\s]+)', r'from datetime import \1, timezone', content, count=1)
             print("Patched import via regex")

    with open("patched_attendance_v3.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix_imports()
