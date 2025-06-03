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


def check_bet_time_v3(cursor, database_table):
    """
    Deletes expired rows from the given database table based on the current UTC time.
    """
    if database_table not in ("lines_data", "all_data"):
        raise ValueError("Invalid table name. Must be 'lines_data' or 'all_data'.")

    # Execute a DELETE query where commence_time has passed
    query = f"DELETE FROM {database_table} WHERE commence_time < %s;"
    cursor.execute(query, (date_time,))
    print(f"Expired entries deleted from {database_table}.")

def clear_bet_table(cursor, database_table):
    """
    Clears the table to enter the new lines and event rows.
    :param cursor:
    :param database_table:
    :return:
    """

    delete_query = f"DELETE FROM {database_table};"
    cursor.execute(delete_query)