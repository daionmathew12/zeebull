import traceback
from app.database import engine
from sqlalchemy import text
import json

try:
    with engine.connect() as conn:
        branches = conn.execute(text("SELECT id FROM branches")).scalars().all()
        for branch_id in branches:
            print(f'Checking roles for branch {branch_id}')
            existing = conn.execute(text("SELECT id FROM roles WHERE name='admin' AND branch_id=:b"), {"b": branch_id}).scalar()
            if not existing:
                empty_perms = json.dumps([])
                conn.execute(text("INSERT INTO roles (name, permissions, branch_id) VALUES ('admin', :p, :b)"), {"p": empty_perms, "b": branch_id})
                conn.execute(text("INSERT INTO roles (name, permissions, branch_id) VALUES ('guest', :p, :b)"), {"p": empty_perms, "b": branch_id})
                print(f'Created admin and guest for branch {branch_id}')
        conn.commit()
except Exception as e:
    traceback.print_exc()
