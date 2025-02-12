#!/bin/bash

# Navigate to the application directory
cd /var/app/current

# Activate the virtual environment
source /var/app/venv/bin/activate

sudo yum install postgresql-devel

# Install any missing dependencies
/var/app/staging-LQM1lest/bin/pip install -r requirements.txt

# Stop any existing process using the server
sudo pkill -f index.py

# Start the application inside the virtual environment
nohup python3 index.py > app.log 2>&1 &

echo "Application restarted successfully!"

