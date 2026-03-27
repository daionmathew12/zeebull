import sys

config_path = '/etc/nginx/sites-enabled/zeebull'

with open(config_path, 'r') as f:
    lines = f.readlines()

orchid_api_block = """
    location /inventoryapi/ {
        proxy_pass http://127.0.0.1:8011/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /inventory/ {
        alias /var/www/html/inventory/;
        try_files $uri $uri/ /inventory/index.html;
    }

    location /orchidadmin/ {
        alias /var/www/resort/Resort_first/dasboard/build/;
        try_files $uri $uri/ /orchidadmin/index.html;
    }
"""

new_lines = []
in_port_80_block = False
port_80_start_idx = -1
last_ssl_brace_idx = -1

for i, line in enumerate(lines):
    if 'listen 443' in line:
        # We are in the SSL block. The closing brace for this block is what we need.
        # Find the next closing brace at column 0
        for j in range(i, len(lines)):
            if lines[j].strip() == '}':
                last_ssl_brace_idx = j
                break
    
    if 'listen 80' in line:
        in_port_80_block = True

# We want to insert BEFORE the closing brace of the SSL block
if last_ssl_brace_idx != -1:
    lines.insert(last_ssl_brace_idx, orchid_api_block)

# Now remove any /inventoryapi/ from the end of the file if it exists in the port 80 block
final_lines = []
skip = False
for line in lines:
    if 'location /inventoryapi/' in line:
        skip = True
    if skip:
        if line.strip() == '}':
            # Check if this is the closing brace of the location block, not the server block
            # Actually, let's just look for the specific block
            pass
        if 'proxy_set_header X-Forwarded-Proto $scheme;' in line:
            # This is the last line of the block before the }
            continue
        if skip and line.strip() == '}' and not any(k in line for k in ['location', 'proxy', 'alias']):
             # This might be the closing brace of the location or server.
             # To be safe, let's just filter out the specific lines.
             continue

# Simpler logic: Reconstruct the file.
# 1. Find the SSL block's final brace.
# 2. Insert Orchid blocks.
# 3. Remove everything after the port 80 'return 404;' before the final brace.

clean_lines = []
ssl_brace_found = False
for i, line in enumerate(lines):
    if 'listen 443' in line:
        # Find closing brace
        brace_idx = -1
        for j in range(i, len(lines)):
            if lines[j].strip() == '}':
                brace_idx = j
                break
        if brace_idx != -1:
            # Add all lines up to brace_idx
            clean_lines.extend(lines[:brace_idx])
            clean_lines.append(orchid_api_block)
            clean_lines.append("}\n")
            # Now add the rest but filter out the bad /inventoryapi/
            rest = lines[brace_idx+1:]
            in_bad_block = False
            for rline in rest:
                if 'location /inventoryapi/' in rline:
                    in_bad_block = True
                if not in_bad_block:
                    clean_lines.append(rline)
                if in_bad_block and rline.strip() == '}':
                    # We might need to keep the final brace of the server block
                    # Let's see if there's another brace after it
                    pass
                if 'proxy_set_header X-Forwarded-Proto $scheme;' in rline:
                    in_bad_block = False
                    # The NEXT brace should be skipped
                    continue
            break

# Actually, the most robust way is to just define the whole config if I can, 
# but I don't want to break Zeebull. 
# Let's just fix the bad append.

final_config = "".join(clean_lines)
with open('zeebull_fixed.conf', 'w') as f:
    f.write(final_config)
print("Fixed config written to zeebull_fixed.conf")
