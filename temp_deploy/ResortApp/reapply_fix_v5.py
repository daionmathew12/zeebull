
import sys

# New calling logic (Fixing Asset Detection & Rentable Flag)
new_call_logic = [
    '                # 2. Process Rented and Standard Good batches\n',
    '                # Define issues lists\n',
    '                good_rented_issues = [d for d in issue_details if (getattr(d, "rental_price", 0) or 0) > 0]\n',
    '                good_issues = [d for d in issue_details if d not in good_rented_issues]\n',
    '                \n',
    '                is_asset_type = False\n',
    '                # Improved Asset Detection\n',
    '                # 1. Check if rentable (Rentals are assets)\n',
    '                if getattr(item, "is_rentable", False):\n',
    '                    is_asset_type = True\n',
    '                # 2. Check if Fixed Asset\n',
    '                elif getattr(item, "is_asset_fixed", False):\n',
    '                    is_asset_type = True\n',
    '                # 3. Check Category attributes (handle missing "type" attr safely)\n',
    '                elif item.category:\n',
    '                    cat_type = getattr(item.category, "type", "") or ""\n',
    '                    if cat_type == "asset":\n',
    '                         is_asset_type = True\n',
    '                    elif getattr(item.category, "is_asset_fixed", False):\n',
    '                         is_asset_type = True\n',
    '                    # Hack: Check known asset categories by name if type is missing\n',
    '                    elif "appliance" in getattr(item.category, "name", "").lower():\n',
    '                         is_asset_type = True\n',
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

# New process_batch definition (Including is_rentable)
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
    '                    # Name Decoration\n',
    '                    if is_asset_type:\n',
    '                        if is_rent_split: display_name += " (Rented)"\n',
    '                    else:\n',
    '                        if payable_qty > 0 and complimentary_qty > 0: display_name += " (Comp/Payable)"\n',
    '                        elif payable_qty > 0: display_name += " (Payable)"\n',
    '                    \n',
    '                    if key not in items_dict:\n',
    '                        # Determine is_rentable flag for UI logic\n',
    '                        # If it is a rent split, it is definitely rentable.\n',
    '                        # Otherwise, inherit from item.\n',
    '                        is_rentable = is_rent_split or getattr(item, "is_rentable", False)\n',
    '                        \n',
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
    '                            "check_stock_compatibility": getattr(item, "check_stock_compatibility", False),\n',
    '                            "item_id": item.id,\n',
    '                            "unit": item.unit,\n',
    '                            "unit_price": item.unit_price or 0,\n',
    '                            "charge_per_unit": item.selling_price or item.unit_price or 0,\n',
    '                            "complimentary_limit": item.complimentary_limit or 0,\n',
    '                            # New required field for Asset/Consumable splitting in UI\n',
    '                            "is_rentable": is_rentable,\n',
    '                            "is_fixed_asset": getattr(item, "is_asset_fixed", False)\n',
    '                        }\n',
    '                    \n',
    '                    items_dict[key]["current_stock"] += qty\n',
    '                    items_dict[key]["complimentary_qty"] += complimentary_qty\n',
    '                    items_dict[key]["payable_qty"] += payable_qty\n'
]


f_path = '/var/www/inventory/ResortApp/app/api/checkout.py'
lines = open(f_path).readlines()

# 1. Locate process_batch - B1
b1_start = -1
b1_end = -1
for i, l in enumerate(lines):
    if 'def process_batch(' in l:
        b1_start = i
    if b1_start != -1 and b1_end == -1 and 'if permanently_mapped_qty > 0:' in l:
        b1_end = i

# 2. Locate calling logic - B2
b2_start = -1
b2_end = -1
for i, l in enumerate(lines):
    if i > 500:
        if '# 2. Process Rented' in l:
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
    
    with open('/tmp/checkout_fixed_final_v5.py', 'w') as out:
        out.writelines(part1 + part2 + part3 + part4 + part5)
    print('SUCCESS')
else:
    print('FAILED to find markers')
