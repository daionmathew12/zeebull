#!/bin/bash
# Deploy updated nginx configuration to server

echo "Deploying nginx configuration to server..."

# Copy nginx.conf to server
scp -i "C:\Users\pro\.ssh\gcp_key" nginx.conf basilabrahamabdulkader@34.93.186.233:/tmp/nginx.conf

# SSH into server and update nginx config
ssh -i "C:\Users\pro\.ssh\gcp_key" basilabrahamabdulkader@34.93.186.233 << 'EOF'
    echo "Backing up current nginx config..."
    sudo cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.backup.$(date +%Y%m%d_%H%M%S)
    
    echo "Installing new nginx config..."
    sudo cp /tmp/nginx.conf /etc/nginx/sites-enabled/default
    
    echo "Testing nginx configuration..."
    sudo nginx -t
    
    if [ $? -eq 0 ]; then
        echo "Configuration valid. Reloading nginx..."
        sudo systemctl reload nginx
        echo "Nginx reloaded successfully!"
    else
        echo "Configuration test failed. Restoring backup..."
        sudo cp /etc/nginx/sites-enabled/default.backup.* /etc/nginx/sites-enabled/default
        echo "Backup restored. Please check the configuration."
        exit 1
    fi
EOF

echo "Deployment complete!"
