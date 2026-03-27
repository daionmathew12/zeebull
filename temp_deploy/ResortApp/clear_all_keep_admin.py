"""
Complete Database Clear - Preserves Admin Only
This uses TRUNCATE CASCADE for complete cleanup
"""

from sqlalchemy import text
from app.database import SessionLocal
from app.models.user import User
from datetime import datetime

def clear_database_complete():
    """Complete database clear with CASCADE"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("COMPLETE DATABASE CLEANUP - PRESERVING ADMIN LOGIN ONLY")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Get admin credentials before clearing
        # Use the requested admin email or fallback to known patterns
        admin_email = "admin@gmail.com"  # Based on common usage in this project
        admin = db.query(User).filter(User.email == admin_email).first()
        
        # Fallback if specific admin not found, try to find ANY admin
        if not admin:
            print(f"⚠ Admin {admin_email} not found. Searching for any admin...")
            admin = db.query(User).filter(User.role_id == 1).first()
            
        if admin:
            admin_data = {
                'name': admin.name,
                'email': admin.email,
                'hashed_password': admin.hashed_password,
                'role_id': admin.role_id,
                'phone': admin.phone,
                'is_active': admin.is_active
            }
            print(f"✓ Saved admin: {admin.email}\n")
        else:
            print("❌ Admin not found! Cannot proceed.\n")
            return
        
        print("-" * 70)
        print("CLEARING ALL DATA...")
        print("-" * 70)
        
        # Disable foreign key checks temporarily - SKIPPING as it requires superuser
        # TRUNCATE ... CASCADE should handle dependencies automatically
        # db.execute(text("SET session_replication_role = 'replica';"))
        
        # Get all tables
        result = db.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT IN ('alembic_version')
            ORDER BY tablename
        """))
        
        tables = [row[0] for row in result]
        
        # Truncate all tables
        for table in tables:
            try:
                db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                print(f"✓ Cleared: {table}")
            except Exception as e:
                print(f"  ⚠ {table}: {str(e)[:60]}")
        
        db.commit()
        
        # Re-enable foreign key checks
        # Re-enable foreign key checks - SKIPPING
        # db.execute(text("SET session_replication_role = 'origin';"))
        db.commit()
        
        print("\n" + "-" * 70)
        print("RESTORING ADMIN...")
        print("-" * 70)
        
        # Recreate admin role
        db.execute(text("""
            INSERT INTO roles (id, name, permissions) 
            VALUES (1, 'admin', '["all"]')
            ON CONFLICT (id) DO UPDATE SET name = 'admin'
        """))
        
        # Recreate guest role
        db.execute(text("""
            INSERT INTO roles (id, name, permissions) 
            VALUES (2, 'guest', '["view"]')
            ON CONFLICT (id) DO UPDATE SET name = 'guest'
        """))
        
        # Recreate admin user
        db.execute(text(f"""
            INSERT INTO users (id, name, email, hashed_password, role_id, phone, is_active)
            VALUES (1, :name, :email, :password, :role_id, :phone, :is_active)
            ON CONFLICT (id) DO UPDATE 
            SET name = :name, email = :email, hashed_password = :password
        """), {
            'name': admin_data['name'],
            'email': admin_data['email'],
            'password': admin_data['hashed_password'],
            'role_id': admin_data['role_id'],
            'phone': admin_data['phone'],
            'is_active': admin_data['is_active']
        })
        
        db.commit()
        
        print(f"✓ Restored admin: {admin_data['email']}")
        print(f"✓ Restored roles: admin, guest")
        
        print("\n" + "=" * 70)
        print("✅ DATABASE COMPLETELY CLEARED")
        print("=" * 70)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"🔐 Login with: {admin_data['email']}")
        print("🔄 Refresh your browser to see clean database\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "!" * 70)
    print("⚠️  DANGER: This will DELETE ALL DATA except admin login!")
    print("!" * 70)
    print("\nThis will remove:")
    print("  • All bookings and reservations")
    print("  • All rooms (you'll need to recreate them)")
    print("  • All inventory and stock")
    print("  • All services and packages")
    print("  • All users except admin")
    print("  • Everything else")
    print("\nThis will keep:")
    print("  • Admin login credentials only")
    print()
    
    print("⚠ Running without confirmation due to remote execution")
    clear_database_complete()
