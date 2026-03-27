
import sys

# New calling logic (With Definitions & Fix applied)
new_call_logic = [
    '                # 2. Process Rented and Standard Good batches\n',
    '                # Define issues lists\n',
    '                good_rented_issues = [d for d in issue_details if (getattr(d, "rental_price", 0) or 0) > 0]\n',
    '                good_issues = [d for d in issue_details if d not in good_rented_issues]\n',
    '                \n',
    '                is_asset_type = False\n',
    '                try:\n',
    '                    if item.category and getattr(item.category, "type", "") == "asset":\n',
    '                        is_asset_type = True\n',
    '                except:\n',
    '                    pass\n',
    '                \n',
    '                item_type_str = "Asset" if is_asset_type else "Consumable"\n',
    '                \n',
    '                if is_asset_type:\n',
    '                    if rented_stock_qty > 0:\n',
    '                        process_batch(rented_stock_qty, good_rented_issues, "_rented", True)\n',
    '                    if standard_stock_qty > 0:\n',
    '                        process_batch(standard_stock_qty, good_issues, "", False)\n',
    '                else:\n',
    '                    # Consumables: Process ALL issues (issue_details) in one batch\n',
    '                    process_batch(issued_stock_qty, issue_details, "", False)\n'
]

f_path = '/var/www/inventory/ResortApp/app/api/checkout.py'
lines = open(f_path).readlines()

# 1. Locate calling block (B2 only, B1 is fine from v2)
b2_start = -1
b2_end = -1

for i, l in enumerate(lines):
    if i > 500:
        # Match the header I added in v2/v1
        if '# 2. Process Rented' in l:
            b2_start = i
    
    if b2_start != -1 and b2_end == -1 and 'for mapping in asset_mappings:' in l:
        b2_end = i

print(f'B2: {b2_start}-{b2_end}')

if b2_start != -1 and b2_end != -1:
    part1 = lines[:b2_start]
    part2 = new_call_logic
    part3 = lines[b2_end:]
    
    with open('/tmp/checkout_fixed_final_v3.py', 'w') as out:
        out.writelines(part1 + part2 + part3)
    print('SUCCESS')
else:
    print('FAILED to find markers')
