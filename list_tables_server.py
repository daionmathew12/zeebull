#!/usr/bin/env python3
"""
Lists all actual tables in zeebulldb.
"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"))
    tables = [r[0] for r in res]
    print(f"Tables ({len(tables)} total):")
    for t in tables:
        print(f"  {t}")
