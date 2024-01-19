from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import time
from scripts.main import run_script
import os
import psycopg2


app = Flask(__name__)


def update_bet_data():
    """
    Call the run function, run_script, from the main file to update the data regarding
    the postive value bets.
    :return:
    """

    dbconn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='admin',
        host='localhost',
        port='5432',
    )

    cur = dbconn.cursor()

    run_script(dbconn, cur)

    cur.close()
    dbconn.close()

    print("The script was run at: ", time.strftime("%Y-%m-%d %H:%M:%S"))


# Your function that performs the task
def run_task():
    # Perform the task here (e.g., running your Python script)
    print("Task running at:", time.strftime("%Y-%m-%d %H:%M:%S"))


# Endpoint to trigger the task manually
@app.route('/trigger-task', methods=['GET'])
def trigger_task():
    update_bet_data()
    return jsonify({'message': 'Task triggered manually'})


# Initializing scheduler for a 15-minute interval
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(run_task, 'interval', minutes=15)
scheduler.start()


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))


