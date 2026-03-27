import sqlite3
import os

db_path = 'ResortApp/resort.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, branch_id, is_superadmin FROM users")
    users = cursor.fetchall()
    print("Users:")
    for user in users:
        print(user)
    
    cursor.execute("SELECT id, name FROM branches")
    branches = cursor.fetchall()
    print("\nBranches:")
    for branch in branches:
        print(branch)
    conn.close()
