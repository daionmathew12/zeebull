"""
Fix all report files - run from c:/releasing/New Orchid/ResortApp
"""
import re, os

BASE = os.path.dirname(os.path.abspath(__file__))

def fix_triple_nested_filter(text):
    # Replace triple-nested branch filter with clean single conditional
    triple = re.compile(
        r'\(\(db\.query\(([^)]+)\)\.filter\(\1\.branch_id == branch_id\) if branch_id is not None else db\.query\(\1\)\)'
        r'\.filter\(\1\.branch_id == branch_id\) if branch_id is not None else '
        r'\(db\.query\(\1\)\.filter\(\1\.branch_id == branch_id\) if branch_id is not None else db\.query\(\1\)\)\)'
    )
    return triple.sub(
        r'(db.query(\1).filter(\1.branch_id == branch_id) if branch_id is not None else db.query(\1))',
        text
    )

# --- Fix reports_module.py ---
filepath = os.path.join(BASE, 'app', 'api', 'reports_module.py')
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
before = content.count('branch_id is not None')
fixed = fix_triple_nested_filter(content)
after = fixed.count('branch_id is not None')
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(fixed)
print(f'reports_module.py: branch_id checks {before} -> {after} (reduced by {before-after})')

# --- Fix comprehensive_reports.py (InventoryCategory has no branch_id) ---
filepath2 = os.path.join(BASE, 'app', 'api', 'comprehensive_reports.py')
with open(filepath2, 'r', encoding='utf-8') as f:
    content2 = f.read()
# Check what line 140 does exactly
lines = content2.splitlines()
for i in range(135, 145):
    print(f'comprehensive L{i+1}: {lines[i]}')
# Replace InventoryCategory.branch_id with InventoryItem.branch_id
fixed2 = content2.replace('InventoryCategory.branch_id', 'InventoryItem.branch_id')
with open(filepath2, 'w', encoding='utf-8') as f:
    f.write(fixed2)
print(f'comprehensive_reports.py: Fixed InventoryCategory.branch_id')

# --- Fix gst_reports.py (InventoryItem has no branch_id) ---
filepath3 = os.path.join(BASE, 'app', 'api', 'gst_reports.py')
with open(filepath3, 'r', encoding='utf-8') as f:
    content3 = f.read()
lines3 = content3.splitlines()
for i in range(916, 926):
    print(f'gst L{i+1}: {lines3[i]}')
fixed3 = content3.replace('InventoryItem.branch_id', 'True  # InventoryItem has no branch_id')
with open(filepath3, 'w', encoding='utf-8') as f:
    f.write(fixed3)
print(f'gst_reports.py: Fixed InventoryItem.branch_id')

print('\nDone!')
