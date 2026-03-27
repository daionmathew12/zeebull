with open('/var/log/orchid/error.log', 'r') as f:
    lines = f.readlines()
    for line in lines[-100:]:
        print(line.strip())
