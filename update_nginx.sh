#!/bin/bash
# Check if /inventoryapi/ already exists to avoid duplicates
if grep -q "location /inventoryapi/" /etc/nginx/sites-enabled/zeebull; then
    echo "Nginx config already updated."
else
    # Insert before the last closing brace
    # remove the last line (assuming it is })
    sudo sed -i '$d' /etc/nginx/sites-enabled/zeebull
    
    # Append the new block and the closing brace
    sudo tee -a /etc/nginx/sites-enabled/zeebull > /dev/null <<EOT
    location /inventoryapi/ {
        proxy_pass http://127.0.0.1:8011/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOT
    echo "Nginx config updated."
fi
sudo nginx -t && sudo systemctl reload nginx
