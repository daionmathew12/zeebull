import re
import os

file_path = r"c:\releasing\New Orchid\ResortApp\app\api\reports_module.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# Add get_branch_id import if missing
if "from app.utils.branch_scope import get_branch_id" not in code:
    code = code.replace(
        "from app.utils.auth import get_current_user",
        "from app.utils.auth import get_current_user\nfrom app.utils.branch_scope import get_branch_id"
    )

# Function to patch each API endpoint to use branch filters
# Regex finds every FastAPI get route in reports_module.py
pattern = r"(@router\.get\([^\)]+\)\s*(?:@apply_api_optimizations\s*)?def \w+\([\s\S]*?(?=\):\s*\"\"\"|:\n\s*\"\"\"))"

# We will manually parse things as it's safer
lines = code.split("\n")
patched_lines = []

in_route = False
current_route = []
modified_count = 0

for idx, line in enumerate(lines):
    # Check if we're hitting def that has Depends(get_current_user)
    if "current_user: dict = Depends(get_current_user)" in line and "def " not in line:
        # Check if following lines or previous lines are part of the function signature
        if "branch_id" not in "".join(current_route):  # Avoid double injection
            # Inject branch_id right before current_user
            indent = line[:line.find("current_user")]
            patched_lines.append(f"{indent}branch_id: Optional[int] = Depends(get_branch_id),")
            modified_count += 1
    
    patched_lines.append(line)

code = "\n".join(patched_lines)

# Now we need to update `db.query(` occurrences to filter by branch_id if applicable.
# This requires replacing `query = db.query(Model)` with:
# `query = db.query(Model)`
# `if branch_id is not None:`
# `    query = query.filter(Model.branch_id == branch_id)`
# We will do a generic approach:
models_with_branch = ["Booking", "PackageBooking", "Checkout", "FoodOrder", "PurchaseMaster", "InventoryTransaction", "Expense", "Employee", "Attendance", "Leave"]

def inject_branch_filters(text):
    for model in models_with_branch:
        # Basic query definition
        search1 = f"db.query({model})"
        if search1 in text:
            repl1 = search1 + f".filter({model}.branch_id == branch_id) if branch_id is not None else " + search1
            # We must be careful not to break chained methods like .filter() or .options().
            # A safer way to inject:
            # db.query(Model).filter(Model.branch_id == branch_id)
            pass
            
            # Since this is too complex for simple replace without syntax tree, let's use a simpler heuristic:
            # In the reports module, almost every query starts with:
            # bookings = db.query(Booking).filter(...)
            # query = db.query(FoodOrder).filter(...)
    
    return text

# Note: Automatic AST or regex modifications for SQLAlchemy queries are deeply complex and error-prone.
# So I will do it simpler: we'll simply append `filter(Model.branch_id == branch_id)` right after `db.query(Model)`

for model in models_with_branch:
    # We replace db.query(Model) with db.query(Model).filter(Model.branch_id == branch_id if branch_id is not None else True)
    # Wait, SQLAlchemy doesn't support "True" natively like that without importing text. 
    # Let's use: db.query(Model).filter(model.branch_id == branch_id) but only conditionally.
    # Actually, a better way is to wait. Python evaluates it. 
    # Just do: db.query(Model).filter(Model.branch_id == branch_id)
    # Wait, if branch_id is None (Superadmin all branches), we shouldn't filter!
    
    # We can use: db.query(Model).filter(Model.branch_id == branch_id if branch_id else Model.branch_id == Model.branch_id)
    # Wait, filter(Model.branch_id == branch_id) if it is None evaluates to IS NULL in SQL.
    pass

# Simplified: we use multi_replace directly in python using re
new_code = code
for m in models_with_branch:
    # Pattern to find db.query(X) and add the conditional filter
    # We will replace `db.query(Model)` with `(db.query(Model).filter(Model.branch_id == branch_id) if branch_id is not None else db.query(Model))`
    # This works for any chain as it evaluates to a Query object.
    replacement = f"(db.query({m}).filter({m}.branch_id == branch_id) if branch_id is not None else db.query({m}))"
    new_code = new_code.replace(f"db.query({m})", replacement)
    
with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_code)

print(f"Patched {modified_count} endpoints. Saved to {file_path}")
