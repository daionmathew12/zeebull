import traceback
from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id FROM branches ORDER BY id LIMIT 1")).scalar()
        print('Using branch id:', res)
        
        try:
            conn.execute(text("ALTER TABLE roles ADD COLUMN branch_id INTEGER REFERENCES branches(id) ON DELETE CASCADE"))
            print('Added branch_id')
        except Exception as e:
            if 'already exists' not in str(e): raise e

        # remove uniqueness on name
        res_con = conn.execute(text("SELECT conname FROM pg_constraint WHERE conrelid = 'roles'::regclass AND contype = 'u'"))
        constraints = [r[0] for r in res_con]
        for c in constraints:
            conn.execute(text(f"ALTER TABLE roles DROP CONSTRAINT {c}"))
            print('Dropped constraint', c)
            
        try:
            conn.execute(text("ALTER TABLE roles ADD CONSTRAINT uq_roles_name_branch UNIQUE (name, branch_id)"))
            print('Added composite unique constraint')
        except Exception as e:
            if 'already exists' not in str(e): raise e

        if res:
            conn.execute(text(f"UPDATE roles SET branch_id = {res} WHERE branch_id IS NULL"))
            print('Updated existing roles to branch', res)

        conn.commit()
        print('DONE.')
except Exception as e:
    print('Failed:', e)
