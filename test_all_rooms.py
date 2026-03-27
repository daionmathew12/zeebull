from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb')
with engine.connect() as conn:
    res = conn.execute(text("SELECT id, number, status FROM rooms ORDER BY id"))
    print("All Rooms:", [dict(r._mapping) for r in res])
