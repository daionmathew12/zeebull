from sqlalchemy import create_engine, inspect
import os

db_url = "postgresql+psycopg2://orchid_user:admin123@localhost/zeebulldb"
engine = create_engine(db_url)
inspector = inspect(engine)

print("--- DATABASE SCHEMA ---")
for table_name in inspector.get_table_names():
    cols = [c['name'] for c in inspector.get_columns(table_name)]
    print(f"Table: {table_name}")
    print(f"Columns: {', '.join(cols)}")
    print("-" * 20)
