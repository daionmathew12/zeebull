"""
Nuclear Database Clear - Removes EVERYTHING including admin
Then recreates admin from scratch
"""

from sqlalchemy import text
from app.database import SessionLocal
from datetime import datetime
import bcrypt

def nuclear_clear():
    """Complete nuclear clear - removes everything, recreates admin"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("🔥 NUCLEAR DATABASE CLEAR - REMOVING EVERYTHING")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("-" * 70)
        print("STEP 1: DISABLING CONSTRAINTS...")
        print("-" * 70)
        
        # Disable all triggers and constraints
        db.execute(text("SET session_replication_role = 'replica';"))
        db.commit()
        print("✓ Constraints disabled\n")
        
        print("-" * 70)
        print("STEP 2: TRUNCATING ALL TABLES...")
        print("-" * 70)
        
        # Get all tables
        result = db.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT IN ('alembic_version')
            ORDER BY tablename
        """))
        
        tables = [row[0] for row in result]
        print(f"Found {len(tables)} tables to clear\n")
        
        # Truncate all tables with CASCADE
        for table in tables:
            try:
                db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                print(f"✓ {table}")
            except Exception as e:
                print(f"  ⚠ {table}: {str(e)[:50]}")
        
        db.commit()
        print(f"\n✓ All tables truncated\n")
        
        print("-" * 70)
        print("STEP 3: RE-ENABLING CONSTRAINTS...")
        print("-" * 70)
        
        # Re-enable constraints
        db.execute(text("SET session_replication_role = 'origin';"))
        db.commit()
        print("✓ Constraints re-enabled\n")
        
        print("-" * 70)
        print("STEP 4: CREATING FRESH ADMIN...")
        print("-" * 70)
        
        # Create admin role
        db.execute(text("""
            INSERT INTO roles (id, name, permissions) 
            VALUES (1, 'admin', '["all"]')
        """))
        print("✓ Created admin role")
        
        # Create guest role
        db.execute(text("""
            INSERT INTO roles (id, name, permissions) 
            VALUES (2, 'guest', '["view"]')
        """))
        print("✓ Created guest role")
        
        # Create admin user with fresh password
        # Password: admin123
        password = "admin123"
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        db.execute(text("""
            INSERT INTO users (id, name, email, hashed_password, role_id, phone, is_active)
            VALUES (1, 'Admin', 'admin@orchid.com', :password, 1, NULL, true)
        """), {'password': hashed})
        print("✓ Created admin user")
        
        db.commit()
        
        print("\n" + "=" * 70)
        print("✅ NUCLEAR CLEAR COMPLETED")
        print("=" * 70)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("🔐 NEW LOGIN CREDENTIALS:")
        print("   Email: admin@orchid.com")
        print("   Password: admin123")
        print()
        print("⚠️  IMPORTANT:")
        print("   1. Refresh your browser (Ctrl+Shift+R for hard refresh)")
        print("   2. Clear browser cache if needed")
        print("   3. Log in with the new credentials above")
        print()
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔥 NUCLEAR CLEAR - This will DELETE EVERYTHING!\n")
    print("This will:")
    print("  • Delete ALL data including admin")
    print("  • Reset all ID sequences to 1")
    print("  • Create fresh admin with password: admin123")
    print()
    
    nuclear_clear()
