import http.client as client
import uuid
from datetime import datetime, timezone
import json

from scripts.dbmanager import check_bet_time_v2
from scripts.utilities import pull_event_lines

apiKey = "098b369ca52dc641b2bea6c901c24887"
host = "api.the-odds-api.com"

conn = client.HTTPSConnection(host)

# Add the sports and market arrays
sports = ['americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_nba', 'basketball_ncaab', 'baseball_mlb',
          'mma_mixed_martial_arts']
betting_markets = ['h2h', 'spreads', 'totals']
# sports = ['mma_mixed_martial_arts']
# betting_markets = ['h2h']
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
    This function takes in the raw data from the API, but doesn't actually pull it, and sorts it into an array that can
    actually be used in the program.
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
                #This means that the line linked in the event object is the same as the line linked in the lines data
                line_id = id_creator

                key = y['key']
                last_update = y['last_update']
                outcomes = y['outcomes']

                line_object = {
                    'uid': line_id,
                    'key': key,
                    'last_update': last_update,
                    'commence_time': commence_time,
                    'outcomes': outcomes,
                    'book': book,
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


def get_data(connection, cur):
    """
    This function actually makes the http calls to the API to get the data. It first calls a database clean up, then
    calls the data, then passes it to games_loop_call to format, then it checks each event in the all_market array for
    duplicates, then it deletes duplicate events and lines, then it adds the event to the database table.
    :param connection:
    :param cur:
    :return:
    """

    clean_up_prep(cur)
    connection.commit()
    print("Clean up complete...")

    # This grabs all the lines from the api and pushes them to the all_markets array
    for s in sports:
        for m in betting_markets:
            url = "/v4/sports/" + s + "/odds/?regions=us&oddsFormat=american&markets=" + m + "&apiKey=" + apiKey
            conn.request("GET", url)

            response = conn.getresponse()
            content = response.read()
            parsed = json.loads(content)

            games_loop_call(parsed)

            print("all_markets Array: ", all_markets)

    for x in all_markets:
        markets = [json.dumps(x['markets'])]
        duplicate_exists = False

        # If a duplicate exists, delete the old one and the olds ones lines and then insert the new one and its lines.
        # It should honestly be as simple as that.

        # Rebuilt duplicate check
        # Check for a value in all data table that matches our value in all_market array
        sql_check = ("SELECT * FROM all_data WHERE event = %s AND commence_time = %s AND home_team"
                     "= %s AND away_team = %s AND sport_key = %s AND sport_title = %s")
        check_data = (x["event"], x['commence_time'], x['home_team'], x['away_team'], x['sport_key'], x['sport_name'])
        cur.execute(sql_check, check_data)

        # Get the first result
        check_result = cur.fetchone()
        print("Check result is: ", check_result)

        # Check if the result exists
        if check_result:
            print("Duplicate Event: ", check_result)
            delete_array = pull_event_lines(check_result)

            # Run another for loop to delete all the lines, this step could be streamlined if working
            for line in delete_array:
                delete_line_sql = "DELETE from lines_data WHERE uid = %s"
                cur.execute(delete_line_sql, (line,))
                print("Line Deleted: ", line)

            # Finally, delete the line and move the cursor.
            print("Event Deleted: ", check_result[0])
            delete_event_sql = ("DELETE FROM all_data WHERE uid = %s")
            cur.execute(delete_event_sql, (check_result[0],))

        # Add the new event regardless of any of the above stuff
        add_new_event_sql = ("INSERT INTO all_data (uid, event, commence_time, update_time, home_team, away_team, "
                             "sport_key, sport_title, markets) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::json[])")
        insert_data = (x['uid'], x["event"], x['commence_time'], x['update_time'], x['home_team'], x['away_team'],
                       x['sport_key'], x['sport_name'], markets)
        cur.execute(add_new_event_sql, insert_data)
        print("Event Added: ", x['uid'])

    # Here, the lines are inserted with no duplication check. The duplication check should be caught by the previous
    # check
    for y in all_lines:
        sql = ("INSERT INTO lines_data (uid, key, last_update, outcomes, commence_time, book) VALUES "
               "(%s, %s, %s, %s::json[], %s, %s)")

        outcomes = [json.dumps(y['outcomes'])]

        data = (y['uid'], y['key'], y['last_update'], outcomes, y['commence_time'], y['book'])

        cur.execute(sql, data)

    connection.commit()