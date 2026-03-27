import sys

config_path = '/etc/nginx/sites-enabled/zeebull'

try:
    with open(config_path, 'r') as f:
        lines = f.readlines()

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

    # Clean up the file first by removing all previous Orchid attempts
    # and identifying the main blocks.
    
    ssl_block_lines = []
    port_80_block_lines = []
    
    current_block = None
    
    for line in lines:
        if 'listen 443' in line:
            current_block = 'ssl'
        if 'listen 80' in line:
            current_block = '80'
            
        # Skip any lines that look like our orchid blocks if they were already added
        if any(x in line for x in ['/inventoryapi/', '/inventory/', '/orchidadmin/']):
            continue
            
        if current_block == 'ssl':
            ssl_block_lines.append(line)
        elif current_block == '80':
            port_80_block_lines.append(line)
        else:
            # Lines before any block (if any, like upstream)
            ssl_block_lines.append(line)

    # Reconstruct from scratch
    final_content = []
    
    # Process SSL block: Find the LAST brace at col 0
    ssl_text = "".join(ssl_block_lines)
    # We assume 'server {' started it. 
    # Let's find the LAST '}' at the start of a line.
    
    # Actually, a better way:
    # Everything before 'listen 80' server block is SSL block.
    # We find the '}' that closes the SSL 'server {' block.
    
    # Split into lines again for easier processing
    ssl_lines = ssl_text.splitlines(keepends=True)
    last_brace_idx = -1
    for i in range(len(ssl_lines)-1, -1, -1):
        if ssl_lines[i].strip() == '}':
            last_brace_idx = i
            break
            
    if last_brace_idx != -1:
        final_content.extend(ssl_lines[:last_brace_idx])
        final_content.extend(orchid_blocks)
        final_content.append("}\n")
    else:
        # Fallback
        final_content.extend(ssl_lines)
        
    # Process Port 80 block: Just keep the basics
    found_return = False
    for line in port_80_block_lines:
        final_content.append(line)
        if 'return 404;' in line:
            final_content.append("}\n")
            break
            
    with open('zeebull_final.conf', 'w') as f:
        f.writelines(final_content)
    print("Final config written to zeebull_final.conf")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
