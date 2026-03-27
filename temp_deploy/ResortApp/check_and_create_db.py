import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
print(f"Testing raw psycopg2 connection to: {db_url}")

try:
    # Try connecting to 'postgres' first to see if server is up
    conn = psycopg2.connect("user='postgres' password='qwerty123' host='localhost' port='5432' dbname='postgres' connect_timeout=5")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database;")
    dbs = [row[0] for row in cur.fetchall()]
    print(f"Available databases: {dbs}")
    
    if 'orchiddb' not in dbs:
        print("Creating 'orchiddb'...")
        cur.execute("CREATE DATABASE orchiddb;")
        print("Database 'orchiddb' created successfully.")
    else:
        print("'orchiddb' exists.")
    
    cur.close()
    conn.close()
    
    # Now try the actual URL
    conn = psycopg2.connect(db_url, connect_timeout=5)
    print("Successfully connected to 'orchiddb'!")
    conn.close()

except Exception as e:
    print(f"Error: {e}")
