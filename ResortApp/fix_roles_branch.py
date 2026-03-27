import traceback
from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        print('Modifying roles table...')
        # 1. Add branch_id
        try:
            conn.execute(text('ALTER TABLE roles ADD COLUMN branch_id INTEGER REFERENCES branches(id) ON DELETE CASCADE'))
            print('Added branch_id to roles')
        except Exception as e:
            if 'already exists' in str(e):
                print('branch_id already exists')
            else:
                raise e

        # 2. Drop unique constraint on 'name'
        res = conn.execute(text("SELECT conname FROM pg_constraint WHERE conrelid = 'roles'::regclass AND contype = 'u'"))
        constraints = [r[0] for r in res]
        for c in constraints:
            print(f'Dropping constraint {c}')
            conn.execute(text(f'ALTER TABLE roles DROP CONSTRAINT {c}'))
        
        # 3. Add composite unique constraint
        try:
            conn.execute(text('ALTER TABLE roles ADD CONSTRAINT uq_roles_name_branch UNIQUE (name, branch_id)'))
            print('Added composite unique constraint')
        except Exception as e:
            if 'already exists' in str(e):
                print('Composite constraint already exists')
            else:
                raise e
                
        # 4. Set branch_id = 1 for existing rows where null
        conn.execute(text('UPDATE roles SET branch_id = 1 WHERE branch_id IS NULL'))

        conn.commit()
        print('Successfully modified roles table.')
except Exception as e:
    print('Error:')
    traceback.print_exc()
