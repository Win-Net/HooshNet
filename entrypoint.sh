#!/bin/bash

# Function to wait for MySQL
wait_for_mysql() {
    echo "Waiting for MySQL..."
    while ! mysqladmin ping -h"$MYSQL_HOST" --silent; do
        sleep 1
    done
    echo "MySQL is up - executing command"
}

# Wait for database
# We need to install mysql-client in Dockerfile to use mysqladmin, or use python to check
# For simplicity, let's use a python one-liner or just sleep a bit if mysql-client is not there.
# But I added default-libmysqlclient-dev and I should add mariadb-client or default-mysql-client to Dockerfile for this tool.
# Let's use a python script to check connection to be safe and dependency-free (since we have python).

echo "Waiting for Database..."
python3 -c "
import time
import mysql.connector
from mysql.connector import Error

while True:
    try:
        conn = mysql.connector.connect(
            host='$MYSQL_HOST',
            user='$MYSQL_USER',
            password='$MYSQL_PASSWORD',
            port=$MYSQL_PORT
        )
        if conn.is_connected():
            print('Database connected!')
            conn.close()
            break
    except Error as e:
        print(f'Waiting for database: {e}')
        time.sleep(2)
"

# Run Migrations
echo "Running Database Migrations..."
# Force Rebuild 2024-12-29
python3 -c "from professional_database import ProfessionalDatabaseManager; db = ProfessionalDatabaseManager(); db.init_database()"

# Start Supervisor
echo "Starting Supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
