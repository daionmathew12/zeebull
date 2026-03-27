#!/usr/bin/env python3
"""
Database Migration Script for Orchid Resort
Run this script on the production server to add missing columns.

Usage:
    cd ResortApp
    source venv/bin/activate
    python3 migrate_database.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SQLALCHEMY_DATABASE_URL

def migrate_database():
    """Add missing columns to various tables."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("=" * 60)
        print("Orchid Resort - Comprehensive Database Migration")
        print("=" * 60)
        print()

        # Helper to add column if not exists
        def add_column(table, column, type_def):
            try:
                # Check column existence using information_schema
                check_sql = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
                result = db.execute(check_sql).fetchone()
                if not result:
                    print(f"Adding {column} to {table}...")
                    db.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"))
                    db.commit()
                    print(f"✓ Successfully added '{column}' to {table}")
                else:
                    print(f"- Column '{column}' already exists in {table}")
            except Exception as e:
                print(f"⚠️  Error adding {column} to {table}: {e}")
                db.rollback()

        # Table: packages
        print("Migrating 'packages' table...")
        add_column('packages', 'booking_type', 'VARCHAR(50) DEFAULT \'room_type\'')
        add_column('packages', 'room_types', 'TEXT')
        add_column('packages', 'status', 'VARCHAR DEFAULT \'active\'')
        add_column('packages', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        print()

        # Table: rooms (Features)
        print("Migrating 'rooms' table features...")
        room_features = [
            'air_conditioning', 'wifi', 'bathroom', 'living_area', 'terrace', 
            'parking', 'kitchen', 'family_room', 'bbq', 'garden', 'dining', 'breakfast'
        ]
        for feat in room_features:
            add_column('rooms', feat, 'BOOLEAN DEFAULT FALSE')
        print()

        # Table: service_requests
        print("Migrating 'service_requests' table...")
        add_column('service_requests', 'billing_status', 'VARCHAR')
        add_column('service_requests', 'started_at', 'TIMESTAMP')
        print()

        # Table: package_bookings
        print("Migrating 'package_bookings' table...")
        add_column('package_bookings', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        print()

        add_column('assigned_services', 'started_at', 'TIMESTAMP')
        add_column('assigned_services', 'completed_at', 'TIMESTAMP')
        add_column('assigned_services', 'override_charges', 'DOUBLE PRECISION')
        print()

        # Table: inventory_transactions
        print("Migrating 'inventory_transactions' table...")
        add_column('inventory_transactions', 'source_location_id', 'INTEGER REFERENCES locations(id)')
        add_column('inventory_transactions', 'destination_location_id', 'INTEGER REFERENCES locations(id)')
        print()

        # Table: food_orders
        print("Migrating 'food_orders' table...")
        add_column('food_orders', 'prepared_by_id', 'INTEGER REFERENCES employees(id)')
        print()

        # Diagnostic: Print last 5 food orders
        print("\nChecking last 5 food orders for diagnostics...")
        orders_sql = text("SELECT id, status, assigned_employee_id, prepared_by_id FROM food_orders ORDER BY id DESC LIMIT 5")
        orders = db.execute(orders_sql).fetchall()
        for o in orders:
            print(f"Order ID: {o[0]}, Status: {o[1]}, AssignedTo: {o[2]}, PreparedBy: {o[3]}")
        print()

        print("=" * 60)
        print("✅ Database migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()
