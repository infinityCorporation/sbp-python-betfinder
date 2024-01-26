#This is the file for the main import loop for the bet data values. This will pull
#the values and push them to a holding database. From that database or table, the
#values can be pulled.

#The idea of this file is keep the costs of requests down the number of calculations
#computed by the program to a reasonable level, between: 10,000,000 - 200,000,000 / day.

# Lines_data needs a commence time for lines to be cleared once the event has finished

import http.client as client
import uuid
from datetime import datetime, timezone
import json

from scripts.dbmanager import check_bet_time_v2

apiKey = "098b369ca52dc641b2bea6c901c24887"
host = "api.the-odds-api.com"

conn = client.HTTPSConnection(host)

# Add the sports and market arrays
# sports = ['americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_nba', 'basketball_ncaab']
# betting_markets = ['h2h', 'spreads', 'totals']
sports = ['americanfootball_nfl']
betting_markets = ['h2h']
current_utc_time = datetime.now(timezone.utc)
date_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')

all_markets = []
all_lines = []

# Pull the data from the api
# From the API an array is sent with the following structure:
# - [Array] Upcoming Games (a)
#   - Game Information
#   - [Array] All Bookmakers (x)
#       - [Array] Markets (y)
#           - Bookmaker Information
#           - [Array] Outcomes (current odds) (z)
#               - [Object] Team Name and Odds


# The start method should be as follows:
# - Check the timing of existing bets
# - Pull new bets
#   - Check all events and then the corresponding lines against existing bets
# - Send confirmation to other processors that import is complete

# Here the issue is that with the split of lines and events, the event may not change while the lines do change. Here,
# consider updating lines instead of chagning the entire row and uid. This only needs to happen on lines that are
# updated for a current event

def clean_up_prep(cursor):
    """
    This functions purpose is to clean up the database and prep it for another data pull. The idea is to clear any
    events that have ended, been cancelled, or duplicates.
    :param cursor:
    :return:
    """
    check_bet_time_v2(cursor, "lines_data")
    check_bet_time_v2(cursor, "all_data")

def games_loop_call(parsed_url):
    """
    The loop pull all necessary objects from the API and stores them in the
    database table all_data_games
    :param parsed_url:
    :return:
    """
    for a in parsed_url:

        uid = str(uuid.uuid4())
        event = a['home_team'] + " vs " + a['away_team']
        commence_time = a['commence_time']
        update_time = date_time
        home_team = a['home_team']
        away_team = a['away_team']
        sport_key = a['sport_key']
        sport_name = a['sport_title']
        markets = []

        for x in a["bookmakers"]:
            id_creator = str(uuid.uuid4())

            book = x['key']
            book_title = x['title']
            lines = id_creator

            for y in x['markets']:
                line_id = id_creator
                print(lines + " and " + line_id)

                key = y['key']
                last_update = y['last_update']
                outcomes = y['outcomes']

                line_object = {
                    'uid': line_id,
                    'key': key,
                    'last_update': last_update,
                    'commence_time': commence_time,
                    'outcomes': outcomes,
                }
                all_lines.append(line_object)

            bookmaker_object = {
                'book': book,
                'title': book_title,
                'lines': lines,
            }
            markets.append(bookmaker_object)

        event_object = {
            'uid': uid,
            'event': event,
            'commence_time': commence_time,
            'update_time': update_time,
            'home_team': home_team,
            'away_team': away_team,
            'sport_key': sport_key,
            'sport_name': sport_name,
            'markets': markets,
        }

        print(event_object)
        all_markets.append(event_object)

# Save to its own table - create table named all_data
# - add columns later today...
def get_data(connection, cur):
    clean_up_prep(cur)

    for s in sports:
        for m in betting_markets:
            url = "/v4/sports/" + s + "/odds/?regions=us&oddsFormat=american&markets=" + m + "&apiKey=" + apiKey
            conn.request("GET", url)

            response = conn.getresponse()
            content = response.read()
            parsed = json.loads(content)

            games_loop_call(parsed)

            print(all_markets)

    for x in all_markets:
        sql = ("INSERT INTO all_data (uid, event, commence_time, update_time, home_team, away_team, sport_key, "
               "sport_title, markets) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::json[])")
        uid = x['uid']
        event = x["event"]
        commence_time = x['commence_time']
        update_time = x['update_time']
        home_team = x['home_team']
        away_team = x['away_team']
        sport_key = x['sport_key']
        sport_title = x['sport_name']
        markets = [json.dumps(x['markets'])]

        print(markets)
        data = (uid, event, commence_time, update_time, home_team, away_team, sport_key, sport_title, markets)

        cur.execute(sql, data)
        connection.commit()

        print("A row was successfully added to: all_data")

    for y in all_lines:
        sql = "INSERT INTO lines_data (uid, key, last_update, outcomes, commence_time) VALUES (%s, %s, %s, %s::json[], %s)"

        uid = y['uid']
        key = y['key']
        last_update = y['last_update']
        commence_time = y['commence_time']
        outcomes = [json.dumps(y['outcomes'])]

        data = (uid, key, last_update, outcomes, commence_time)

        cur.execute(sql, data)
        connection.commit()

        print("Row was successfully added to: lines_data")