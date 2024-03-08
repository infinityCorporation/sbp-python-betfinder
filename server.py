from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import time
from scripts.positiveev import run_script
from scripts.data_import import get_data
from scripts.arbitrage import arbitrage_main
import os
import psycopg2


app = Flask(__name__)

#New main flow:
# - Import full bet list
# - Save it to database
# - Call the data in rotating order to the following:
#   - Arbitrage
#   - Positive EV
#   - Scanner
# - Save the processed information to separate database tables
# - Sort for Arbitrage and Positive EV
# - Return values upon called from server.py


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


def pull_all_data_games():
    """
    This function is intended to assist the /pull-data endpoint.
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

    get_data(dbconn, cur)

    cur.close()
    dbconn.close()


def main_stack():
    dbconn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='admin',
        host='localhost',
        port='5432',
    )

    cur = dbconn.cursor()

    get_data(dbconn, cur)
    arbitrage_main(dbconn, cur)

    cur.close()
    dbconn.close()


def arbitrage_call():
    dbconn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='admin',
        host='localhost',
        port='5432',
    )

    cur = dbconn.cursor()

    arbitrage_main(dbconn, cur)

    cur.close()
    dbconn.close()


# Your function that performs the task
def run_task():
    # Perform the task here (e.g., running your Python script)
    print("Task running at:", time.strftime("%Y-%m-%d %H:%M:%S"))


# Endpoints
@app.route('/trigger-task', methods=['GET'])
def trigger_task():
    update_bet_data()
    return jsonify({'message': 'Task triggered manually'})


@app.route('/pull-data', methods=['GET'])
def pull_data():
    pull_all_data_games()
    return jsonify({'message': 'Task has been triggered.'})


@app.route('/run-stack', methods=['GET'])
def run_full_stack():
    main_stack()
    return jsonify({'message': 'The Main Stack has finished running.'})


@app.route('/arb-test', methods=['GET'])
def run_arbitrage():
    arbitrage_call()
    return jsonify({'message': 'The arbitrage test has finished running.'})


# Initializing scheduler for a 15-minute interval
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(run_task, 'interval', minutes=15)
scheduler.start()


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))


