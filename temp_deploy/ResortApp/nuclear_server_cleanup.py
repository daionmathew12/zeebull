
import os
import subprocess

TABLES_TO_KEEP = {
    'users', 'roles', 'rooms', 'employees', 'vendors', 
    'inventory_items', 'inventory_categories', 
    'food_items', 'food_categories', 'services', 'packages',
    'unit_conversions', 'units_of_measurement', 'alembic_version',
    'housekeeping_tasks', 'departments'
}

def clear_server_thoroughly():
    pem = r"C:\Users\pro\.ssh\gcp_key"
    ip = "34.30.59.169"
    user = "basilabrahamaby"
    db = "orchid_resort"
    db_pass = "admin123"
    db_user = "orchid_user"
    
    # 1. Get all tables
    cmd_list = f'ssh -o StrictHostKeyChecking=no -i "{pem}" {user}@{ip} "export PGPASSWORD=\'{db_pass}\'; psql -h localhost -U {db_user} -d {db} -t -c \\"SELECT tablename FROM pg_tables WHERE schemaname=\'public\'\\""'
    result = subprocess.run(cmd_list, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error listing tables: {result.stderr}")
        return
        
    all_tables = [t.strip() for t in result.stdout.split('\n') if t.strip()]
    tables_to_clear = [t for t in all_tables if t not in TABLES_TO_KEEP]
    
    print(f"Planning to clear {len(tables_to_clear)} tables...")
    
    # 2. Build one big command
    truncate_cmds = [f'TRUNCATE TABLE \\"{t}\\" CASCADE;' for t in tables_to_clear]
    # Update master data
    update_cmds = [
        "UPDATE rooms SET status = 'Available', housekeeping_status = 'Clean', housekeeping_updated_at = NULL;",
        "UPDATE inventory_items SET current_stock = 0.0;"
    ]
    
    full_sql = " ".join(truncate_cmds + update_cmds)
    
    cmd_exec = f'ssh -o StrictHostKeyChecking=no -i "{pem}" {user}@{ip} "export PGPASSWORD=\'{db_pass}\'; psql -h localhost -U {db_user} -d {db} -c \\"{full_sql}\\""'
    
    print("Executing cleanup...")
    result_exec = subprocess.run(cmd_exec, shell=True, capture_output=True, text=True)
    
    if result_exec.returncode == 0:
        print("✅ Server cleanup completed successfully!")
        print(result_exec.stdout)
    else:
        print(f"❌ Cleanup failed: {result_exec.stderr}")

if __name__ == "__main__":
    clear_server_thoroughly()
