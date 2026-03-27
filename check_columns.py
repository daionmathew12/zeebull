from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb')
with engine.connect() as conn:
    print("Checking bookings table columns:")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'bookings'"))
    for r in res:
        print(r[0])
    
    print("\nChecking package_bookings table columns:")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'package_bookings'"))
    for r in res:
        print(r[0])
