from app.utils.auth import get_db
from app.models.branch import Branch
from sqlalchemy.orm import Session
import os
import sys

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.utils.auth import get_db

db_gen = get_db()
db = next(db_gen)

try:
    branches = db.query(Branch).all()
    for b in branches:
        print(f"ID: {b.id}, Name: {b.name}")
finally:
    db.close()
