import sys

config_path = '/etc/nginx/sites-enabled/zeebull'

try:
    with open(config_path, 'r') as f:
        lines = f.readlines()

    # Define the blocks to add
    orchid_blocks = [
        "\n",
        "    # Orchid Backend API\n",
        "    location /inventoryapi/ {\n",
        "        proxy_pass http://127.0.0.1:8011/;\n",
        "        proxy_set_header Host $host;\n",
        "        proxy_set_header X-Real-IP $remote_addr;\n",
        "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n",
        "        proxy_set_header X-Forwarded-Proto $scheme;\n",
        "    }\n",
        "\n",
        "    # Orchid User Frontend\n",
        "    location /inventory/ {\n",
        "        alias /var/www/html/inventory/;\n",
        "        try_files $uri $uri/ /inventory/index.html;\n",
        "    }\n",
        "\n",
        "    # Orchid Admin Dashboard\n",
        "    location /orchidadmin/ {\n",
        "        alias /var/www/resort/Resort_first/dasboard/build/;\n",
        "        try_files $uri $uri/ /orchidadmin/index.html;\n",
        "    }\n"
    ]

    new_content = []
    ssl_closing_brace_index = -1
    
    # 1. Find the closing brace of the FIRST server block (SSL block)
    # We look for a line with just '}' after 'listen 443'
    found_443 = False
    for i, line in enumerate(lines):
        if 'listen 443' in line:
            found_443 = True
        if found_443 and line.strip() == '}':
            ssl_closing_brace_index = i
            break
            
    if ssl_closing_brace_index == -1:
        print("Could not find SSL closing brace")
        sys.exit(1)

    # 2. Extract port 80 block start
    port_80_start_index = -1
    for i in range(ssl_closing_brace_index + 1, len(lines)):
        if 'listen 80' in line or 'server {' in lines[i]:
             # Find the NEXT server block
             if 'server {' in lines[i]:
                 port_80_start_index = i
                 break
    
    # 3. Build new content
    # Parts: 
    # - Start of SSL block
    # - Orchid blocks
    # - SSL block closing brace
    # - Port 80 block up to 'return 404;'
    # - Port 80 block closing brace
    
    new_content.extend(lines[:ssl_closing_brace_index])
    new_content.extend(orchid_blocks)
    new_content.append("}\n")
    
    # Now find the port 80 block parts
    port_80_lines = lines[ssl_closing_brace_index + 1:]
    found_80_server = False
    for line in port_80_lines:
        if 'server {' in line:
            found_80_server = True
        if found_80_server:
            new_content.append(line)
            if 'return 404;' in line:
                new_content.append("}\n")
                break
                
    with open('zeebull_clean.conf', 'w') as f:
        f.writelines(new_content)
    print("Clean config written to zeebull_clean.conf")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
