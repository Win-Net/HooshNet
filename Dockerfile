FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    git \
    cron \
    nginx \
    supervisor \
    procps \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn supervisor

# Copy project files
COPY . .

# Create directory for logs and backups
RUN mkdir -p logs backups database_backups

# Setup Nginx
RUN rm /etc/nginx/sites-enabled/default
COPY nginx.conf /etc/nginx/sites-available/vpn_bot
RUN ln -s /etc/nginx/sites-available/vpn_bot /etc/nginx/sites-enabled/

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 80 443 5000

# Entrypoint
ENTRYPOINT ["/entrypoint.sh"]
