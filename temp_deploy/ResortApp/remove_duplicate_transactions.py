#!/usr/bin/env python3
# Remove duplicate transaction tracking from cleanup code

with open(r'c:\releasing\orchid\ResortApp\app\api\checkout.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 2613-2622 (InventoryTransaction creation)
new_lines = []
for i, line in enumerate(lines):
    line_num = i + 1
    if 2613 <= line_num <= 2622:
        # Skip these lines - they create duplicate transactions
        continue
    new_lines.append(line)

# Write back
with open(r'c:\releasing\orchid\ResortApp\app\api\checkout.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Removed duplicate transaction creation (lines 2613-2622)")
print("   Stock movements are already tracked by Stock Issue")
