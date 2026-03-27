
import sys

# New process_batch definition
new_process_batch = [
    '                def process_batch(qty, issues, key_suffix, is_rent_split):\n',
    '                    remaining = float(qty)\n',
    '                    payable_qty = 0.0\n',
    '                    complimentary_qty = 0.0\n',
    '                    \n',
    '                    issue_idx = 0\n',
    '                    while remaining > 0:\n',
    '                        take = 0\n',
    '                        if issue_idx < len(issues):\n',
    '                            issue = issues[issue_idx]\n',
    '                            needed = float(issue.issued_quantity)\n',
    '                            take = min(remaining, needed)\n',
    '                            # Check if payable\n',
    '                            is_pay = False\n',
    '                            if (getattr(issue, "rental_price", 0) or 0) > 0: is_pay = True\n',
    '                            if getattr(issue, "is_payable", False): is_pay = True\n',
    '                            \n',
    '                            if is_pay:\n',
    '                                payable_qty += take\n',
    '                            else:\n',
    '                                complimentary_qty += take\n',
    '                            issue_idx += 1\n',
    '                        else:\n',
    '                            # Surplus stock is usually complimentary (or just unconsumed stock)\n',
    '                            complimentary_qty += remaining\n',
    '                            take = remaining\n',
    '                        remaining -= take\n',
    '                    \n',
    '                    key = f"{item.id}{key_suffix}"\n',
    '                    display_name = item.name\n',
    '                    if is_asset_type:\n',
    '                        if is_rent_split: display_name += " (Rented)"\n',
    '                    else:\n',
    '                        if payable_qty > 0 and complimentary_qty > 0: display_name += " (Comp/Payable)"\n',
    '                        elif payable_qty > 0: display_name += " (Payable)"\n',
    '                    \n',
    '                    if key not in items_dict:\n',
    '                        items_dict[key] = {\n',
    '                            "id": item.id,\n',
    '                            "item_code": item.item_code,\n',
    '                            "item_name": display_name,\n',
    '                            "current_stock": 0.0,\n',
    '                            "complimentary_qty": 0.0,\n',
    '                            "payable_qty": 0.0,\n',
    '                            "category_id": item.category_id,\n',
    '                            "is_payable": is_rent_split or (payable_qty > 0),\n',
    '                            "item_type": item_type_str,\n',
    '                            "check_stock_compatibility": item.check_stock_compatibility,\n',
    '                            "item_id": item.id\n',
    '                        }\n',
    '                    \n',
    '                    items_dict[key]["current_stock"] += qty\n',
    '                    items_dict[key]["complimentary_qty"] += complimentary_qty\n',
    '                    items_dict[key]["payable_qty"] += payable_qty\n'
]

# New calling logic
new_call_logic = [
    '                # 2. Process Rented and Standard Good batches\n',
    '                if is_asset_type:\n',
    '                    if rented_stock_qty > 0:\n',
    '                        process_batch(rented_stock_qty, good_rented_issues, "_rented", True)\n',
    '                    if standard_stock_qty > 0:\n',
    '                        process_batch(standard_stock_qty, good_issues, "", False)\n',
    '                else:\n',
    '                    # Consumables: Process in ONE batch to mix comp/payable in single row\n',
    '                    process_batch(issued_stock_qty, good_issues, "", False)\n'
]

f_path = '/var/www/inventory/ResortApp/app/api/checkout.py'
lines = open(f_path).readlines()

# 1. Locate process_batch
b1_start = -1
b1_end = -1
for i, l in enumerate(lines):
    if 'def process_batch(' in l:
        b1_start = i
    if b1_start != -1 and b1_end == -1 and 'if permanently_mapped_qty > 0:' in l:
        b1_end = i # End at the start of next logic block

# 2. Locate calling block
b2_start = -1
b2_end = -1
for i, l in enumerate(lines):
    if i > 500 and 'if is_asset_type:' in l: # Ensure it is the logic block
        b2_start = i
    if b2_start != -1 and b2_end == -1 and 'for mapping in asset_mappings:' in l:
        b2_end = i

print(f'B1: {b1_start}-{b1_end}, B2: {b2_start}-{b2_end}')

if b1_start != -1 and b1_end != -1 and b2_start != -1 and b2_end != -1:
    part1 = lines[:b1_start]
    part2 = new_process_batch
    part3 = lines[b1_end:b2_start]
    part4 = new_call_logic
    part5 = lines[b2_end:]
    
    with open('/tmp/checkout_fixed_final.py', 'w') as out:
        out.writelines(part1 + part2 + part3 + part4 + part5)
    print('SUCCESS')
else:
    print('FAILED to find markers')
