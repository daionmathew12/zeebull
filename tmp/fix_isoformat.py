import os, re
api_dir = 'ResortApp/app/api'
pattern = re.compile(r'\.isoformat\(\)(?!\s*\+\s*[\'"]Z[\'"])')
count = 0
for root, _, files in os.walk(api_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content, num_subs = pattern.subn('.isoformat() + "Z"', content)
            if num_subs > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += num_subs
                print(f'Replaced {num_subs} in {filepath}')
print(f'Total replacements: {count}')
