import subprocess

def run_ssh(cmd):
    pem = r"C:\Users\pro\.ssh\gcp_key"
    remote = "basilabrahamaby@34.171.13.80"
    full_cmd = f'ssh -o StrictHostKeyChecking=no -i "{pem}" {remote} "{cmd}"'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

def investigate():
    print("--- Databases ---")
    stdout, stderr = run_ssh("export PGPASSWORD='admin123'; psql -h localhost -U orchid_user -d postgres -c \"SELECT datname FROM pg_database;\"")
    print(stdout)
    if stderr: print("ERR:", stderr)

    print("--- Web Directory Contents ---")
    stdout, stderr = run_ssh("sudo find /var/www -maxdepth 2")
    print(stdout)
    if stderr: print("ERR:", stderr)

    print("--- Services ---")
    stdout, stderr = run_ssh("systemctl list-units --type=service --all | grep -E 'zeebull|resort|inventory|nginx'")
    print(stdout)
    if stderr: print("ERR:", stderr)

    print("--- Nginx Configs ---")
    stdout, stderr = run_ssh("ls /etc/nginx/sites-enabled/")
    print(stdout)
    if stderr: print("ERR:", stderr)

if __name__ == "__main__":
    investigate()
