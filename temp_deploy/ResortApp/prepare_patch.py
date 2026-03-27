import os

path = "/home/basilabrahamaby/orchid-repo/ResortApp/app/api/dashboard.py"
with open(path, 'r') as f:
    content = f.read()

marker = 'return [{'
insertion = 'print(f"DEBUG_KPI: {results}")\n        '
# find first occurrence in get_kpis
new_content = content.replace(marker, 'results = [{\n            "checkouts_today": checkouts_today,\n            "checkouts_total": checkouts_total,\n            "available_rooms": available_rooms_count,\n            "booked_rooms": booked_rooms_count,\n            "food_revenue_today": float(food_revenue_today) if food_revenue_today else 0,\n            "package_bookings_today": package_bookings_today,\n        }]\n        print(f"DEBUG_KPI: {results}")\n        return results\n        # ', 1)

# Note: The original return was return [{...}]. I'll use a simpler patch.

patch = """
        results = [{
            "checkouts_today": checkouts_today,
            "checkouts_total": checkouts_total,
            "available_rooms": available_rooms_count,
            "booked_rooms": booked_rooms_count,
            "food_revenue_today": float(food_revenue_today) if food_revenue_today else 0,
            "package_bookings_today": package_bookings_today,
        }]
        print(f"DEBUG_KPI: {results}")
        return results
"""

# Find get_kpis return block
with open(patch_script := 'patch_kpis.py', 'w') as pf:
    pf.write(f'''
import os
path = "{path}"
with open(path, "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "return [" in line and "checkouts_today" in lines[i+1]:
        # Replace return block
        j = i
        while "}]" not in lines[j]:
            j += 1
        lines[i:j+1] = [
            '        res_dict = {{\\n',
            '            "checkouts_today": checkouts_today,\\n',
            '            "checkouts_total": checkouts_total,\\n',
            '            "available_rooms": available_rooms_count,\\n',
            '            "booked_rooms": booked_rooms_count,\\n',
            '            "food_revenue_today": float(food_revenue_today) if food_revenue_today else 0,\\n',
            '            "package_bookings_today": package_bookings_today,\\n',
            '        }}\\n',
            '        print(f"DEBUG_KPI: {{res_dict}}")\\n',
            '        return [res_dict]\\n'
        ]
        break

with open(path, "w") as f:
    f.writelines(lines)
''')
