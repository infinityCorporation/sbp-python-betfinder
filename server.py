from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import time

app = Flask(__name__)

# Your function that performs the task
def run_task():
    # Perform the task here (e.g., running your Python script)
    print("Task running at:", time.strftime("%Y-%m-%d %H:%M:%S"))

# Endpoint to trigger the task manually
@app.route('/trigger-task', methods=['GET'])
def trigger_task():
    run_task()
    return jsonify({'message': 'Task triggered manually'})

# Initializing scheduler for a 15-minute interval
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(run_task, 'interval', minutes=15)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))