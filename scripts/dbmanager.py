# The purpose of this file is to manage the database. It contains most of the functions
# that act on the database in any type of way.

from datetime import datetime, timezone
import psycopg2

current_utc_time = datetime.now(timezone.utc)
date_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def check_duplicates(data_object, cursor):
    """
    When adding data into the database, to keep costs and size down, duplicates should be found and removed. This
    program will take in the current object and the database connection and find and duplicates, completely deleting
    them.
    :param data_object:
    :param cursor:
    :return:
    """

    search_values = (data_object[1], data_object[2], data_object[3], data_object[4], data_object[5], data_object[6],
                     data_object[7], data_object[8], data_object[9])

    search_sql = ("SELECT * FROM bet_data WHERE sport = %s AND game = %s AND book = %s AND direction = %s "
                  "AND type = %s AND value = %s AND probability = %s AND price = %s AND commence_time = %s")
    cursor.execute(search_sql, search_values)
    search_result = cursor.fetchone()

    if search_result is not None:
        delete_sql = ("DELETE FROM bet_data WHERE sport = %s AND game = %s AND book = %s AND direction = %s "
                      "AND type = %s AND value = %s AND probability = %s AND price = %s AND commence_time = %s")
        cursor.execute(delete_sql, search_values)


def check_odds_change(data_object, cursor):
    """
    Often, the odds may change meaning that the bet is no longer available. This means that that object will
    have to be found and deleted. This is a more complicated process but a simplified version will be made first.
    :param data_object:
    :param cursor:
    :return:
    """

    sql_search = ("SELECT * FROM bet_data WHERE sport = %s AND game = %s AND book = %s AND direction = %s "
                  "AND type = %s AND commence_time = %s")
    search_data = (data_object[1], data_object[2], data_object[3], data_object[4], data_object[5], data_object[9])

    cursor.execute(sql_search, search_data)
    result = cursor.fetchone()

    if result is not None:
        sql_delete = ("DELETE FROM bet_data WHERE sport = %s AND game = %s AND book = %s AND "
                      "direction = %s AND type = %s AND commence_time = %s")
        cursor.execute(sql_delete, search_data)


def check_bet_time(cursor):
    """
    To keep the database clean, old bets where the event has passed should be found and deleted. That is the purpose
    of this function. (Note that all database management functions should be moved to a separate file.)
    :param cursor:
    :return:
    """

    sql_search = "SELECT * FROM bet_data"

    cursor.execute(sql_search)

    try:
        while True:
            result = cursor.fetchone()
            print(result)

            if result is None:
                break

            commence_time = result[9]

            commence_value = datetime.strptime(commence_time, '%Y-%m-%dT%H:%M:%SZ')
            current_value = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%SZ')

            if commence_value < current_value:
                key_value = (result[0],)
                delete_sql = "DELETE FROM bet_data WHERE id = %s"

                cursor.execute(delete_sql, key_value)

                print("An expired value was found and deleted")

    except psycopg2.Error as e:
        print("An error occurred:", e)


def test_looping_function(cursor):
    """
    This is a function to test looping through the postgres database.
    :param cursor:
    :return:
    """

