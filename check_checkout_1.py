from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb')
with engine.connect() as conn:
    res = conn.execute(text("SELECT * FROM checkout WHERE booking_id = 1"))
    print("Checkout records for booking 1:")
    for r in res:
        print(dict(r._mapping))
