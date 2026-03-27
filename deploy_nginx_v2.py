import subprocess
import os

config = r'''server {
    listen 80;
    server_name 34.71.114.198;

    # Support for hardcoded /zeebull/ prefix in user frontend
    location /zeebull/ {
        alias /var/www/zeebull/;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # User Frontend (Root)
    location / {
        root /var/www/zeebull;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # zeebulladmin
    location /zeebulladmin/ {
        alias /var/www/zeebull/zeebulladmin/;
        index index.html;
        try_files $uri $uri/ /zeebulladmin/index.html;
    }

    # zeebullapi
    location /zeebullapi/ {
        proxy_pass http://localhost:8013/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Remove /zeebullapi/ from path when forwarding to API
        rewrite ^/zeebullapi/(.*) /$1 break;
    }

    # API docs and other direct API access (if needed)
    location /api/ {
        proxy_pass http://localhost:8013/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
'''

temp_file = 'temp_nginx.conf'
with open(temp_file, 'w') as f:
    f.write(config)

ssh_command = [
    'ssh', '-i', r'C:\Users\pro\.ssh\gcp_key', 
    'basilabrahamaby@34.71.114.198', 
    "sudo tee /etc/nginx/sites-available/zeebull > /dev/null && sudo nginx -t && sudo systemctl restart nginx"
]

try:
    with open(temp_file, 'rb') as f:
        result = subprocess.run(ssh_command, stdin=f, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
finally:
    if os.path.exists(temp_file):
        os.remove(temp_file)
