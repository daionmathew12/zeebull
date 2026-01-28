
from sqlalchemy import create_engine, text
from datetime import date
import os

DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("\n=== CHECK REVENUE DATES ===")
        today = date.today()
        print(f"Server Date: {today}")

        # 1. Check Checkouts Today
        print("\n--- Checkouts Today ---")
        result = connection.execute(text(f"SELECT id, grand_total, checkout_date FROM checkouts WHERE DATE(checkout_date) = '{today}'"))
        checkouts = list(result)
        if checkouts:
            for row in checkouts:
                print(f"ID: {row.id}, Amount: {row.grand_total}, Date: {row.checkout_date}")
        else:
            print("No checkouts today.")

        # 2. Check Bookings Checked-In Today
        print("\n--- Bookings Checked-In Today ---")
        result = connection.execute(text(f"SELECT id, total_amount, check_in, status FROM bookings WHERE check_in = '{today}'"))
        bookings_today = list(result)
        if bookings_today:
            for row in bookings_today:
                print(f"ID: {row.id}, Amount: {row.total_amount}, CheckIn: {row.check_in}, Status: {row.status}")
        else:
            print("No bookings checked in today.")

        # 3. Check All Bookings (Month)
        print("\n--- All Recent Bookings (Last 5) ---")
        result = connection.execute(text("SELECT id, total_amount, check_in, status FROM bookings ORDER BY id DESC LIMIT 5"))
        for row in result:
            print(f"ID: {row.id}, Amount: {row.total_amount}, CheckIn: {row.check_in}, Status: {row.status}")

except Exception as e:
    print(f"Error connecting to DB: {e}")
