import os

file_path = '/var/www/zeebull/ResortApp/gunicorn.conf.py'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith('chdir ='):
        new_lines.append('chdir = "/var/www/zeebull/ResortApp"\n')
    elif stripped.startswith('errorlog ='):
        new_lines.append('errorlog = None\n')
    elif stripped.startswith('accesslog ='):
        new_lines.append('accesslog = None\n')
    else:
        new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)
print("Updated gunicorn.conf.py")
