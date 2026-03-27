import subprocess

def run_ssh():
    pem = r"C:\Users\pro\.ssh\gcp_key"
    cmd = f'ssh -o StrictHostKeyChecking=no -i "{pem}" basilabrahamaby@34.30.59.169 "export PGPASSWORD=\'qwerty123\'; psql -h localhost -U postgres -d postgres -c \\"SELECT datname FROM pg_database;\\""'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

if __name__ == "__main__":
    run_ssh()
