import os

def reveal():
    path = "/home/basilabrahamaby/orchid-repo/ResortApp/.env"
    try:
        with open(path, 'r') as f:
            for line in f:
                if "DATABASE_URL" in line:
                    line = line.strip()
                    print(f"Full Line: {line}")
                    try:
                        # expected: DATABASE_URL=postgresql+psycopg2://user:pass@host/db
                        if "://" in line:
                            after_proto = line.split("://")[1]
                            creds = after_proto.split("@")[0]
                            if ":" in creds:
                                user, password = creds.split(":")
                                print(f"Decoded User: {user}")
                                print(f"Decoded Pass: {password}")
                    except Exception as e:
                        print(f"Parse error: {e}")
    except Exception as e:
        print(f"File error: {e}")

if __name__ == "__main__":
    reveal()
