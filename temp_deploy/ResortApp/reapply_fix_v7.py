
import sys

# New Logic: DISABLE Section 5 Fallback if checkout_request used
# AND fix calculate_consumable_charge call (already OK in helper, but verifying caller)

f_path = '/var/www/inventory/ResortApp/app/api/checkout.py'
lines = open(f_path).readlines()

new_section_5_check = [
    '    # 5. Stock Issues NOT in Audit\n',
    '    # If we have a valid checkout request (audit), we SKIP this fallback section\n',
    '    # to prevent items from appearing that were implicitly or explicitly cleared/ignored in the audit.\n',
    '    if checkout_request and checkout_request.inventory_data:\n',
    '        print(f"[BILLING] Skipping Section 5 Fallback due to active checkout request {checkout_request.id}")\n',
    '        stock_issues = []\n',
    '    else:\n',
    '        stock_issues = (db.query(StockIssue)\n',
    '                        .options(joinedload(StockIssue.details).joinedload(StockIssueDetail.item))\n',
    '                        .filter(StockIssue.destination_location_id == room.inventory_location_id,\n',
    '                                StockIssue.issue_date >= check_in_datetime)\n',
    '                        .all())\n',
    '    \n'
]

# Locate Section 5
s5_start = -1
s5_end = -1
for i, l in enumerate(lines):
    if '# 5. Stock Issues NOT in Audit' in l:
        s5_start = i
    if s5_start != -1 and s5_end == -1 and 'for issue in stock_issues:' in l:
        s5_end = i # This is correct, but we need to replace the db.query part

# Refined slicing
if s5_start != -1:
    # Find WHERE the query ends ( .all() )
    for j in range(s5_start, len(lines)):
        if '.all()' in lines[j] or '.all())' in lines[j]:
            s5_end = j + 1
            break

print(f'S5: {s5_start}-{s5_end}')

if s5_start != -1 and s5_end != -1:
    part1 = lines[:s5_start]
    part2 = new_section_5_check
    part3 = lines[s5_end:]
    
    with open('/tmp/checkout_fixed_final_v7.py', 'w') as out:
        out.writelines(part1 + part2 + part3)
    print('SUCCESS')
else:
    print('FAILED to find markers')
