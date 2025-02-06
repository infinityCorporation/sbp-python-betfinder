from apscheduler.schedulers.background import BackgroundScheduler
import time
from scripts.data_import import get_data
from scripts.arbitrage import arbitrage_main
from scripts.pev2 import ev_main
import psycopg2
from psycopg2 import pool
from flask import Flask, jsonify
import os


app = Flask(__name__)


def get_db_pool():
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dbname='postgres',
        user='postgres',
        password=os.environ["bet_db_pass"],
        host='bet-data.cr086aqucn7m.us-east-2.rds.amazonaws.com',
        port='5432'
    )
    return db_pool.getconn()


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


def pull_all_data_games():
    """
    This function is intended to assist the /pull-data endpoint.
    :return:
    """
    db_connection = get_db_pool()
    cur = db_connection.cursor()
    get_data(db_connection, cur)
    cur.close()
    db_connection.close()


def main_stack():
    db_connection = get_db_pool()
    cur = db_connection.cursor()

    get_data(db_connection, cur)
    arbitrage_main(db_connection, cur)
    ev_main(db_connection, cur)

    cur.close()
    db_connection.close()


def arbitrage_call():
    db_connection = get_db_pool()
    cur = db_connection.cursor()
    arbitrage_main(db_connection, cur)
    cur.close()
    db_connection.close()


def pev2_call():
    db_connection = get_db_pool()
    cur = db_connection.cursor()
    ev_main(cur, db_connection)
    cur.close()
    db_connection.close()


# Your function that performs the task
def run_task():
    # Perform the task here (e.g., running your Python script)
    print("Main stack running at:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("Main stack start... ")
    print("----------------------------------------------------------------")
    try:
        run_full_stack()
        print("----------------------------------------------------------------")
        print("Main stack run successfully")
        print("----------------------------------------------------------------")
    except:
        print("----------------------------------------------------------------")
        print("Main stack encountered an error...")
        print("----------------------------------------------------------------")


# Endpoints
@app.route('/', methods=['GET'])
def root():
    return jsonify({"hello": "world"})


@app.route('/status', methods=['GET'])
def send_status():
    return jsonify({'status': 'up'})


@app.route('/pull-data', methods=['GET'])
def pull_data():
    pull_all_data_games()
    return jsonify({'message': 'New data has been pulled from the API.'})


@app.route('/run-stack', methods=['GET'])
def run_full_stack():
    main_stack()
    return jsonify({'message': 'The Main Stack has finished running.'})


@app.route('/arb-test', methods=['GET'])
def run_arbitrage():
    arbitrage_call()
    return jsonify({'message': 'The arbitrage test has finished running.'})


@app.route('/pev-test', methods=['GET'])
def test_pev():
    pev2_call()
    return jsonify({'message': 'The pev2 test has finished running. '})


scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(run_task, 'interval', minutes=360)
scheduler.start()


if __name__ == '__main__':
    app.run(debug=True, port=8000)



