from scripts.data_import import get_data
import psycopg2
from psycopg2 import pool

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



