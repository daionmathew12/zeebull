#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple script to clear all services"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    exit(1)

from sqlalchemy import create_engine, text

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    trans = conn.begin()
    try:
        print("Deleting assigned services...")
        conn.execute(text("DELETE FROM assigned_services"))
        print("Deleting service inventory items...")
        conn.execute(text("DELETE FROM service_inventory_items"))
        print("Deleting service images...")
        conn.execute(text("DELETE FROM service_images"))
        print("Deleting services...")
        conn.execute(text("DELETE FROM services"))
        trans.commit()
        print("SUCCESS: All services cleared!")
    except Exception as e:
        trans.rollback()
        print(f"ERROR: {e}")
        raise



