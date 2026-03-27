import subprocess

def run_ssh():
    pem = r"C:\Users\pro\.ssh\gcp_key"
    cmd = f'ssh -o StrictHostKeyChecking=no -i "{pem}" basilabrahamaby@34.30.59.169 "export PGPASSWORD=\'admin123\'; psql -h localhost -U orchid_user -l"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("ERR:", result.stderr)

if __name__ == "__main__":
    run_ssh()
