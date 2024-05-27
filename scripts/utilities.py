# Library imports
import json
import numpy as np
import http.client as client

# Class references
from scripts.classes.lineClass import Line


def create_api_connection():
    """
    This function creates an HTTPS connection with the API that provides the sports betting data.
    :return:
    """

    host = "api.the-odds-api.com"
    conn = client.HTTPSConnection(host)

    return conn


def pull_event_lines(event):
    """
    Given an event in what is essentially a json structure, this function will collect all the line uid's for that given
    event and put them into an array which will be returned.
    :param event:
    :return lines[]:
    """

    markets = event[8][0]
    lines = []

    for book in markets:
        lines.append(book['lines'])

    return lines


def event_import_with_duplicate_check(markets, cur):
    """
    Used in the data import files, this function first checks for duplicates, which are deleted if found, then it stores
    the event in the data table "all_data"
    :param markets:
    :param cur:
    :return:
    """

    for x in markets:

        # Check for a value in all data table that matches our value in markets array
        sql_check = ("SELECT * FROM all_data WHERE event = %s AND commence_time = %s AND home_team"
                     "= %s AND away_team = %s AND sport_key = %s AND sport_title = %s AND bet_key = %s")
        check_data = (x["event"], x['commence_time'], x['home_team'], x['away_team'], x['sport_key'], x['sport_name'],
                      x['bet_key'])
        cur.execute(sql_check, check_data)

        # Get the first result
        check_result = cur.fetchone()

        # Check if the result exists, if it does, get the events lines to delete them as well
        if check_result:
            lines_to_delete_array = pull_event_lines(check_result)

            # Once the lines are collected, loop through the array and delete them one at a time
            for line in lines_to_delete_array:
                delete_line_sql = "DELETE from lines_data WHERE uid = %s"
                cur.execute(delete_line_sql, (line,))

            # Once the lines are deleted, delete the duplicate event
            delete_event_sql = "DELETE FROM all_data WHERE uid = %s"
            cur.execute(delete_event_sql, (check_result[0],))

        # Regardless of whether there is a duplicate event, we will add the new event to make sure no data is missed
        add_new_event_sql = ("INSERT INTO all_data (uid, event, commence_time, update_time, home_team, away_team, "
                             "sport_key, sport_title, markets, bet_key) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, "
                             "%s::json[], %s)")
        insert_data = (x['uid'], x["event"], x['commence_time'], x['update_time'], x['home_team'], x['away_team'],
                       x['sport_key'], x['sport_name'], [json.dumps(x['markets'])], x['bet_key'])
        cur.execute(add_new_event_sql, insert_data)
        print("Event Added: ", x['uid'])


def lines_import_without_check(lines, cur):
    """
    Due to the fact that 'event_import_with_duplicate_check' checks lines as well, this function just imports all given
    lines into the 'all_lines' table
    :param lines:
    :param cur:
    :return:
    """

    for y in lines:
        print("line:", y)
        sql = ("INSERT INTO lines_data (uid, key, last_update, outcomes, commence_time, book) VALUES "
               "(%s, %s, %s, %s::json[], %s, %s)")

        try:
            data = (y['uid'], y['key'], y['last_update'], [json.dumps(y['outcomes'])], y['commence_time'], y['book'])
            cur.execute(sql, data)
        except:
            print("There was an error... ")
            print(" ------- ")

        print("Line Added: ", y['uid'])


def compare_lines(first_line, second_line):
    """
    The goal here is to take two lines and compare them, returning a positive line and a negative line as a Line object
    :param first_line:
    :param second_line:
    :return positive_line, negative_line:
    """

    positive_line = Line()
    negative_line = Line()

    if (first_line['price'] is not None and second_line['price'] is not None) and (first_line['price'] != 0
                                                                                   and second_line['price'] != 0):
        if first_line['price'] > second_line['price']:
            positive_line.set_name(first_line['name'])
            positive_line.set_price(int(first_line['price']))
            negative_line.set_name(second_line['name'])
            negative_line.set_price(int(second_line['price']))
        else:
            positive_line.set_name(second_line['name'])
            positive_line.set_price(int(second_line['price']))
            negative_line.set_name(first_line['name'])
            negative_line.set_price(int(first_line['price']))
    else:
        print("Line Error:")
        print("NoneType or Zero found.")

    return positive_line, negative_line


def calculate_probability(odds: int):
    """
    The goal here is to calculate the odds regardless of whether they are positive or negative.
    :param odds:
    :return:
    """
    if odds > 0:
        odds = np.abs(odds)
        return round(((100 / (odds + 100)) * 100), 2)
    elif odds < 0:
        odds = np.abs(odds)
        return round(((odds / (odds + 100)) * 100), 2)


def calculate_two_way_vig(negative_probability, positive_probability):
    """
    This is the new version of calculating the no vig odds and returning the juice.
    :param negative_probability:
    :param positive_probability:
    :return vig, new_positive_price, new_negative_price:
    """

    total_implied = np.abs(negative_probability) + np.abs(positive_probability)

    vig = (1 - ((1 / total_implied) * 100)) * 100
    new_positive_probability = (positive_probability / total_implied) * 100
    new_negative_probability = (negative_probability / total_implied) * 100

    return round(new_negative_probability, 2), round(new_positive_probability, 2)
