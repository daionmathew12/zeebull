from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb')
with engine.connect() as conn:
    res = conn.execute(text("SELECT id, number, status FROM rooms WHERE number = '101' OR number = '102'"))
    print("Room Status:", [dict(r._mapping) for r in res])
    
    res_b = conn.execute(text("SELECT id, status, check_in, check_out FROM bookings WHERE status IN ('booked', 'checked-in') ORDER BY id DESC LIMIT 5"))
    print("Active regular bookings:", [dict(r._mapping) for r in res_b])
    
    res_br = conn.execute(text("""
        SELECT br.booking_id, br.room_id, r.number, b.status, b.guest_name 
        FROM booking_rooms br 
        JOIN rooms r ON br.room_id = r.id 
        JOIN bookings b ON br.booking_id = b.id 
        WHERE r.number = '101' AND b.status IN ('booked', 'checked-in')
    """))
    print("Room 101 active regular bookings:", [dict(r._mapping) for r in res_br])

    res_pbr = conn.execute(text("""
        SELECT pbr.package_booking_id, pbr.room_id, r.number, pb.status, pb.guest_name 
        FROM package_booking_rooms pbr 
        JOIN rooms r ON pbr.room_id = r.id 
        JOIN package_bookings pb ON pbr.package_booking_id = pb.id 
        WHERE r.number = '101' AND pb.status IN ('booked', 'checked-in')
    """))
    print("Room 101 active package bookings:", [dict(r._mapping) for r in res_pbr])
