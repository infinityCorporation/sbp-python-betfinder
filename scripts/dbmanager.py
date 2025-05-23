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


def check_bet_time_v2(cursor, database_table):
    """
    This is a new version of the previous check_bet_time management function. It has the same functionality but an all
    new looping algorithm that should be more stable and throw less errors.
    :param cursor:
    :param database_table:
    :return:
    """
    expired = []

    # Don't need to do it like this... can do
    query = "DELETE FROM " + database_table + "WHERE commence_time < "

    get_all = "SELECT * FROM " + database_table + ";"
    cursor.execute(get_all)

    results = cursor.fetchall()

    for row in results:
        print("Checking timing of event... ")

        if database_table == "lines_data":
            commence_time = row[4]
        elif database_table == "all_data":
            commence_time = row[2]

        commence_value = datetime.strptime(commence_time, '%Y-%m-%dT%H:%M:%SZ')
        current_value = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%SZ')

        # Remember that this is not based on the update_time stored in the database but rather
        # it is based on the actual current time value that python pulls.
        latest = max((commence_value, current_value))
        print(latest)
        print(row)

        if latest == current_value:
            print(" - - - Found an Expired Event - - - ")
            expired.append(row[0])
        elif latest == commence_value:
            print("This event's time value checks out. Moving onto the next ->")

    print(expired)

    for y in expired:
        print(y)
        if database_table == "lines_data":
            delete_all = "DELETE FROM lines_data WHERE uid LIKE %s;"
            cursor.execute(delete_all, (y,))
            print("A lines row may have been deleted... UID: " + y)
        elif database_table == "all_data":
            delete_all = "DELETE FROM all_data WHERE uid LIKE %s;"
            cursor.execute(delete_all, (y,))
            print("A data row may have been deleted... UID: " + y)

