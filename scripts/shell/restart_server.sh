#!/bin/bash

# Navigate to the application directory
cd /var/app/current

# Activate the virtual environment
source /var/app/venv/bin/activate

# Install any missing dependencies
pip install -r requirements.txt

# Stop any existing process using the server
sudo pkill -f server.py

# Start the application inside the virtual environment
nohup python3 server.py > app.log 2>&1 &

echo "Application restarted successfully!"

