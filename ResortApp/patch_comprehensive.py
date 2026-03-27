import re
import os

file_path = r"c:\releasing\New Orchid\ResortApp\app\api\comprehensive_reports.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# Add get_branch_id import if missing
if "from app.utils.branch_scope import get_branch_id" not in code:
    code = code.replace(
        "from app.utils.auth import get_current_user",
        "from app.utils.auth import get_current_user\nfrom app.utils.branch_scope import get_branch_id"
    )

lines = code.split("\n")
patched_lines = []

modified_count = 0

for idx, line in enumerate(lines):
    # Check if we're hitting def that has Depends(get_current_user)
    if "current_user" in line and "Depends(get_current_user)" in line and "def " not in line:
        # Check if following lines or previous lines are part of the function signature
        if "branch_id:" not in "".join(patched_lines[-3:]):  # Avoid double injection
            indent = line[:line.find("current_user")]
            patched_lines.append(f"{indent}branch_id: int | None = Depends(get_branch_id),")
            modified_count += 1
    
    patched_lines.append(line)

code = "\n".join(patched_lines)

models_with_branch = ["Booking", "PackageBooking", "Checkout", "FoodOrder", "PurchaseMaster", "InventoryTransaction", "Expense", "Employee", "Attendance", "Leave", "InventoryItem", "AssignedService"]

new_code = code
for m in models_with_branch:
    replacement = f"(db.query({m}).filter({m}.branch_id == branch_id) if branch_id is not None else db.query({m}))"
    new_code = new_code.replace(f"db.query({m})", replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_code)

print(f"Patched {modified_count} endpoints. Saved to {file_path}")
