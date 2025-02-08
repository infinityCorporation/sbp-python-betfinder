from scripts.data_import import get_data
from scripts.arbitrage import arbitrage_main
from scripts.pev2 import ev_main
import psycopg2
from psycopg2 import pool

# To Get this all running you need to...
# - Connect the code pipeline up with code deploy to ec2 (you left of with fixing the
#   us-east-1 agent and moving it to use-east-2)
# - Confirm that the program is working as expected within ec2
# - Create a cron job that will allow the program to run every hour on the hour (more
#   can be added later)
# - Finally, do some general code cleaning and attempt to prep the program for
#   a production ready version.


def get_db_pool():
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dbname='postgres',
        user='postgres',
        password="managerPass_02",
        host='bet-data.cr086aqucn7m.us-east-2.rds.amazonaws.com',
        port='5432'
    )
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
    arbitrage_main(db_connection, cur)
    ev_main(db_connection, cur)

    print("Closing the existing connections!")
    cur.close()
    db_connection.close()


main()



