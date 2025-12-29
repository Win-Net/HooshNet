#!/bin/bash

# SSL Generation Script
# This script runs inside the container to generate SSL certificates

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ]; then
    echo "Usage: ./generate_ssl.sh <domain> [email]"
    exit 1
fi

echo "Requesting SSL certificate for $DOMAIN..."

# Stop Nginx to free port 80
supervisorctl stop nginx

# Run Certbot
if [ -z "$EMAIL" ]; then
    certbot certonly --standalone -d "$DOMAIN" --register-unsafely-without-email --agree-tos --non-interactive
else
    certbot certonly --standalone -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
fi

# Check if successful
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Certificate generated successfully!"
    
    # Link certificates
    ln -sf "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" /etc/nginx/ssl/fullchain.pem
    ln -sf "/etc/letsencrypt/live/$DOMAIN/privkey.pem" /etc/nginx/ssl/privkey.pem
    
    echo "Certificates linked."
else
    echo "Certificate generation failed!"
    supervisorctl start nginx
    exit 1
fi

# Start Nginx
supervisorctl start nginx
echo "Nginx restarted with new certificate."
