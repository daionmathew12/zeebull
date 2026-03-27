"""
Fix script for all report files:
1. Clean up the triple-nested branch_id filter in reports_module.py (24 occurrences)
2. Fix InventoryCategory.branch_id in comprehensive_reports.py
3. Fix InventoryItem.branch_id in gst_reports.py
"""
import re

def fix_triple_nested_filter(text):
    """
    Replace the ugly pattern:
    (db.query(X).filter(X.branch_id==branch_id) if branch_id is not None else db.query(X)).filter(X.branch_id==branch_id) if branch_id is not None else (db.query(X).filter(X.branch_id==branch_id) if branch_id is not None else db.query(X))
    with simply:
    db.query(X)
    and then add .filter(X.branch_id == branch_id) call separately via a simpler conditional.
    
    Actually the safest approach: replace the full triple-nested ternary with just the db.query() part,
    then after the .options() or .filter() etc, if needed, add a clean conditional filter.
    
    The pattern on a single line always wraps just one model query.
    """
    # Pattern: ((db.query(MODEL).filter(MODEL.branch_id == branch_id) if branch_id is not None else db.query(MODEL)).filter(MODEL.branch_id == branch_id) if branch_id is not None else (db.query(MODEL).filter(MODEL.branch_id == branch_id) if branch_id is not None else db.query(MODEL)))
    
    # Simpler equivalent: (db.query(MODEL).filter(MODEL.branch_id == branch_id) if branch_id is not None else db.query(MODEL))
    
    # Match the triple pattern and collapse to a clean single
    triple = re.compile(
        r'\(\(db\.query\(([^)]+)\)\.filter\(\1\.branch_id == branch_id\) if branch_id is not None else db\.query\(\1\)\)'
        r'\.filter\(\1\.branch_id == branch_id\) if branch_id is not None else '
        r'\(db\.query\(\1\)\.filter\(\1\.branch_id == branch_id\) if branch_id is not None else db\.query\(\1\)\)\)'
    )
    
    fixed = triple.sub(
        r'(db.query(\1).filter(\1.branch_id == branch_id) if branch_id is not None else db.query(\1))',
        text
    )
    return fixed

# ===== Fix reports_module.py =====
with open('app/api/reports_module.py', 'r', encoding='utf-8') as f:
    content = f.read()

original = content
fixed = fix_triple_nested_filter(content)
count = content.count('branch_id is not None') - fixed.count('branch_id is not None')
changes = sum(1 for a, b in zip(content.splitlines(), fixed.splitlines()) if a != b)
with open('app/api/reports_module.py', 'w', encoding='utf-8') as f:
    f.write(fixed)
print(f'reports_module.py: {len(re.findall("branch_id is not None", original))} => {len(re.findall("branch_id is not None", fixed))} branch_id checks, {changes} lines changed')

# ===== Fix comprehensive_reports.py - InventoryCategory.branch_id =====
with open('app/api/comprehensive_reports.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and fix: InventoryCategory doesn't have branch_id
# The filter is on InventoryItem - need to remove InventoryCategory.branch_id filter
content2 = re.sub(
    r'InventoryCategory\.branch_id == branch_id',
    'InventoryItem.branch_id == branch_id',
    content
)
with open('app/api/comprehensive_reports.py', 'w', encoding='utf-8') as f:
    f.write(content2)
print('comprehensive_reports.py: Fixed InventoryCategory.branch_id -> InventoryItem.branch_id')

# ===== Fix gst_reports.py - InventoryItem.branch_id =====
with open('app/api/gst_reports.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and neutralize InventoryItem.branch_id filter (InventoryItem doesn't have branch_id)
lines = content.splitlines(keepends=True)
new_lines = []
for i, line in enumerate(lines):
    if 'InventoryItem.branch_id' in line:
        print(f'  gst_reports.py L{i+1}: Removing InventoryItem.branch_id filter: {line.strip()}')
        # Comment out that filter add
        line = line.replace('InventoryItem.branch_id == branch_id', 'True  # InventoryItem has no branch_id column')
    new_lines.append(line)

with open('app/api/gst_reports.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('gst_reports.py: Fixed InventoryItem.branch_id references')

print('\\nAll fixes applied!')
