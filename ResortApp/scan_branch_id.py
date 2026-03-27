import ast
import os
import glob

api_dir = 'c:/releasing/New Orchid/ResortApp/app/api'

# We want to skip some files where branch_id isn't naturally required or is already handled specially
SKIP_FILES = ['branch.py', 'auth.py', 'settings.py', 'user_app.py']

missing_endpoints = []

for filepath in glob.glob(os.path.join(api_dir, '*.py')):
    filename = os.path.basename(filepath)
    if filename in SKIP_FILES or filename == '__init__.py':
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if it has a route decorator
            is_route = False
            method = ''
            path = ''
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute) and decorator.func.value.id == 'router':
                        is_route = True
                        method = decorator.func.attr
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
            
            if is_route:
                has_branch_id = any(arg.arg == 'branch_id' for arg in node.args.args)
                has_current_user = any(arg.arg == 'current_user' for arg in node.args.args)
                
                # Check kwargs or other ways it might get it? We explicitly look for branch_id arg
                if not has_branch_id:
                    missing_endpoints.append({
                        'file': filename,
                        'func': node.name,
                        'method': method,
                        'path': path
                    })

for m in missing_endpoints:
    print(f"{m['file']} - {m['method'].upper()} {m['path']} - {m['func']}")
print(f"Total endpoints missing branch_id argument: {len(missing_endpoints)}")

