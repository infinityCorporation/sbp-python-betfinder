# Library imports
import json
import uuid
import numpy as np
import http.client as client
import ssl
import requests
from psycopg2.extras import execute_values, Json
from psycopg2.extensions import AsIs


# Class references
from scripts.classes.lineClass import Line

import requests

class APIConnection:
    def __init__(self, base_url="https://api.the-odds-api.com"):
        self.session = requests.Session()
        self.base_url = base_url
        self.response = None

    def request(self, method, path, **kwargs):
        # If path starts with '/', remove it to avoid double slash
        if path.startswith("/"):
            path = path[1:]
        url = f"{self.base_url}/{path}"
        self.response = self.session.request(method, url, **kwargs)

    def getresponse(self):
        return self.response

def create_api_connection():
    return APIConnection()


def pull_event_lines(event):
    """
    Given an event in what is essentially a json structure, this function will collect all the line uid's for that given
    event and put them into an array which will be returned.
    :param event:
    :return lines[]:
    """

    markets = event['markets']
    lines = []

    for book in markets:
        lines.append(book['lines'])

    return lines


def event_import_v2(markets, cur):
    """
    Bulk inserts event data into the all_data table, assuming markets is now a JSONB column.
    """
    sql = """
    INSERT INTO all_data (
        uid, event, commence_time, update_time, home_team, away_team,
        sport_key, sport_title, markets, bet_key
    ) VALUES %s
    """

    values = [
        (
            x['uid'],
            x["event"],
            x['commence_time'],
            x['update_time'],
            x['home_team'],
            x['away_team'],
            x['sport_key'],
            x['sport_name'],
            Json(x['markets']),  # Now a clean single JSONB object
            x['bet_key'],
        )
        for x in markets
    ]

    execute_values(cur, sql, values)
    print(f"{len(values)} events added.")


def lines_import_v2(lines, cur):
    """
    Bulk insert line objects into the 'lines_data' table using execute_values for efficiency.
    """
    sql = """ INSERT INTO lines_data ( uid, key, last_update, outcomes, commence_time, book, team_one, team_two, event,
    event_uid ) VALUES %s
    """


    def adapt_json_array(outcomes):
        # Create a properly escaped PostgreSQL array string like:
        # '{"{\"name\": \"Win\", \"price\": 120}" , "{\"name\": \"Lose\", \"price\": -140}"}'
        return "{" + ",".join(json.dumps(o).replace('"', '\\"').replace("'", "''") for o in outcomes) + "}"

    # Prepare the data as a list of tuples
    values = [
        (
            y['uid'],
            y['key'],
            y['last_update'],
            Json(y['outcomes']),
            y['commence_time'],
            y['book'],
            y['team_one'],
            y['team_two'],
            y['event'],
            y['event_uid'],
        )
        for y in lines
    ]

    execute_values(cur, sql, values)
    print(f"{len(values)} lines added.")


def compare_lines(first_line, second_line):
    """
    The goal here is to take two lines and compare them, returning a positive line and a negative line as a Line object
    :param first_line:
    :param second_line:
    :return positive_line, negative_line:
    """
    positive_uid = str(uuid.uuid4())
    negative_uid = str(uuid.uuid4())

    positive_line = Line()
    negative_line = Line()

    if (first_line['price'] is not None and second_line['price'] is not None) and (first_line['price'] != 0
                                                                                   and second_line['price'] != 0):
        if first_line['price'] > second_line['price']:
            positive_line.uid = positive_uid
            positive_line.set_name(first_line['name'])
            positive_line.set_price(int(first_line['price']))
            negative_line.uid = negative_uid
            negative_line.set_name(second_line['name'])
            negative_line.set_price(int(second_line['price']))
        else:
            positive_line.uid = positive_uid
            positive_line.set_name(second_line['name'])
            positive_line.set_price(int(second_line['price']))
            negative_line.uid = negative_uid
            negative_line.set_name(first_line['name'])
            negative_line.set_price(int(first_line['price']))
    else:
        print("Line Error:")
        print("NoneType or Zero found.")

    return positive_line, negative_line


def calculate_probability(odds):
    """
    The goal here is to calculate the odds regardless of whether they are positive or negative.
    :param odds:
    :return:
    """
    if odds > 0:
        return round(((100 / (odds + 100)) * 100), 2)
    elif odds < 0:
        return round(((abs(odds) / (abs(odds) + 100)) * 100), 2)


def calculate_two_way_vig(negative_probability, positive_probability):
    """
    This is the new version of calculating the no vig odds and returning the juice.
    :param negative_probability:
    :param positive_probability:
    :return vig, new_positive_price, new_negative_price:
    """

    over_round = negative_probability + positive_probability
    vig = (over_round - 100)

    new_positive_probability = (positive_probability - (vig / 2))
    new_negative_probability = (negative_probability - (vig / 2))

    new_positive_price = (100 / (new_positive_probability / 100)) - 100
    new_negative_price = - 100 / (1 - (new_negative_probability / 100)) + 100

    return (abs(round(new_negative_probability, 2)), abs(round(new_positive_probability, 2)),
            round(new_negative_price, 2), round(new_positive_price, 2))

