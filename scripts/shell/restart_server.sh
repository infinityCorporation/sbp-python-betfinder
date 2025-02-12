#!/bin/bash

# Navigate to the application directory
cd /var/app/current

echo "got here"

# Activate the virtual environment
source /var/app/venv/staging-LQM1lest/bin/activate

echo "got here 2"

sudo yum install postgresql-devel

echo "got here 3"

# Install any missing dependencies
/var/app/staging-LQM1lest/bin/pip install -r /var/app/current/build/requirements.txt

echo "got here 4"

# Stop any existing process using the server
sudo pkill -f index.py

echo "got here 5"

# Start the application inside the virtual environment
nohup python3 index.py > app.log 2>&1 &

echo "got here 6"

echo "Application restarted successfully!"

