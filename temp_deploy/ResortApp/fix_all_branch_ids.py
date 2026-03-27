from app.database import SessionLocal, engine
from sqlalchemy import inspection
from sqlalchemy import text
from app.database import Base
from pkgutil import walk_packages
import importlib
import os
import sys

# load all models
models_dir = os.path.join(os.path.dirname(__file__), "app", "models")
for module_info in walk_packages([models_dir], "app.models."):
    importlib.import_module(module_info.name)

missing_branch_id_tables = []
for mapper in Base.registry.mappers:
    cls = mapper.class_
    if hasattr(cls, "__tablename__"):
        table_name = cls.__tablename__
        if hasattr(cls, "branch_id"):
            # Check if this table actually has it in DB
            try:
                with engine.connect() as conn:
                    conn.execute(text(f"SELECT branch_id FROM {table_name} LIMIT 1"))
            except Exception as e:
                # If error is that branch_id column doesn't exist
                if 'does not exist' in str(e):
                    missing_branch_id_tables.append(table_name)

if missing_branch_id_tables:
    print("Tables mapped with branch_id but missing in DB:")
    for t in sorted(set(missing_branch_id_tables)):
        print(t)
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE {t} ADD COLUMN branch_id INTEGER REFERENCES branches(id) ON DELETE SET NULL"))
                conn.commit()
                print(f" -> Added branch_id to {t}!")
        except Exception as e:
            print(f" -> Failed to add branch_id to {t} due to {e}")
else:
    print("All models mapped with branch_id exist in DB.")
