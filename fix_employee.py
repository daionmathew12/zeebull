
import re

def fix_file():
    with open("remote_employee.py", "r") as f:
        content = f.read()

    # Regex to find the get_pending_leaves function
    # It looks for @router.get("/pending-leaves"...) followed by def get_pending_leaves...
    pattern = r'(@router\.get\("/pending-leaves".*?\)\s*\n\s*def get_pending_leaves.*?return .*?\.all\(\)\s*\n)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("Could not find get_pending_leaves function")
        return

    func_code = match.group(1)
    
    # Remove the function from its current place
    new_content = content.replace(func_code, "")
    
    # Insert it before @router.get("/{employee_id}")
    # Find the insertion point
    insert_marker = '@router.get("/{employee_id}")'
    if insert_marker not in new_content:
        print("Could not find insertion point")
        return
        
    parts = new_content.split(insert_marker)
    
    final_content = parts[0] + func_code + "\n" + insert_marker + parts[1]
    
    with open("fixed_employee.py", "w") as f:
        f.write(final_content)
        
    print("File fixed and saved to fixed_employee.py")

if __name__ == "__main__":
    fix_file()
