from scripts.data_import import get_data
from scripts.arbitrage import arbitrage_main
from scripts.pev2 import ev_main
import psycopg2
from psycopg2 import pool
import os

# Goal now is to set up cron jobs


sports = ['basketball_nba', 'basketball_ncaab', 'baseball_mlb', 'americanfootball_nfl', 'americanfootball_ncaaf']

def get_db_pool():
    print("Getting db pool...")
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dbname='postgres',
        user='postgres',
        password="managerPass_02",
        host='bet-data.cr086aqucn7m.us-east-2.rds.amazonaws.com',
        port='5432'
    )
    print("Db pool found...")
    return db_pool.getconn()


def pull_all_data_games():
    """
    This function is intended to assist the /pull-data endpoint.
    :return:
    """
    print("Get Data is running, setting up connections...")
    db_connection = get_db_pool()
    cur = db_connection.cursor()

    print("Calling the main function...")
    get_data(db_connection, cur)

    print("Closing existing connections!")
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


def main():
    """
    This function will be the calling point to run the main stack
    :return:
    """
    print("The main stack is beginning to run...")
    db_connection = get_db_pool()
    cur = db_connection.cursor()

    print("Calling the main functions now...")
    get_data(db_connection, cur)

    print("Closing the existing connections!")
    cur.close()
    db_connection.close()


main()



