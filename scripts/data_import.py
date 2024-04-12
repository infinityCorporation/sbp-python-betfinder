# Library imports
import uuid
from datetime import datetime, timezone
import json

# Script imports
from scripts.dbmanager import check_bet_time_v2
from scripts.alternate_import import alternate_import
from scripts.utilities import event_import_with_duplicate_check, lines_import_without_check, create_api_connection

# frisbiecorp@gmail.com: 5ab51a74ab7fea2414dbade0cf9d7229
# contact@arrayassistant.ai: 098b369ca52dc641b2bea6c901c24887

apiKey = "5ab51a74ab7fea2414dbade0cf9d7229"
conn = create_api_connection()

# Add the sports and market arrays
# sports = ['americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_nba', 'basketball_ncaab', 'baseball_mlb',
#         'mma_mixed_martial_arts']
# betting_markets = ['h2h', 'spreads', 'totals']
sports = ['basketball_nba', 'basketball_ncaab']
betting_markets = ['h2h']
current_utc_time = datetime.now(timezone.utc)
date_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')

# sports = ['basketball_nba', 'basketball_ncaab']
# betting_markets = ['h2h_q1', 'h2h_q2', 'h2h_q3', 'h2h_q4', 'h2h_h1', 'h2h_h2', 'spreads_q1', 'spreads_q2',
#                   'spreads_q3', 'spreads_q4', 'spreads_h1', 'spreads_h2', 'totals_q1', 'totals_q2', 'totals_q3',
#                   'totals_q4', 'totals_h1', 'totals_h2', ]


# Initialize the necessary arrays
all_markets = []
all_lines = []
all_event_ids = []

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

    # Loop through all returned json event objects for a given sport
    for a in parsed_url:

        try:
            uid = str(uuid.uuid4())
            event_id = a['id']
            event = a['home_team'] + " vs " + a['away_team']
            commence_time = a['commence_time']
            update_time = date_time
            home_team = a['home_team']
            away_team = a['away_team']
            sport_key = a['sport_key']
            sport_name = a['sport_title']
            markets = []

            # Add all ids and sport keys for alternative imports
            all_event_ids.append({
                'id': a['id'],
                'key': a['sport_key'],
            })

            # Loop through each bookmaker for a given event
            for x in a["bookmakers"]:
                id_creator = str(uuid.uuid4())

                book = x['key']
                book_title = x['title']
                lines = id_creator

                # Loop through each line in the bookmaker's markets
                for y in x['markets']:

                    line_id = id_creator
                    key = y['key']
                    last_update = y['last_update']
                    outcomes = y['outcomes']

                    # Create a single line object for each line
                    line_object = {
                        'uid': line_id,
                        'key': key,
                        'last_update': last_update,
                        'commence_time': commence_time,
                        'outcomes': outcomes,
                        'book': book,
                    }
                    all_lines.append(line_object)

                # Create an object for each book's info and all lines
                bookmaker_object = {
                    'book': book,
                    'title': book_title,
                    'lines': lines,
                }
                markets.append(bookmaker_object)

            # Finally, create an object with all the event's information
            event_object = {
                'uid': uid,
                'id': event_id,
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

        except NameError:
            print("The line with the error was: ")
            print(json.dumps(a))
        except TypeError:
            print("There was a type err here: ")
            print(json.dumps(a))


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

            print(parsed)

            games_loop_call(parsed)

            print("all_markets Array: ", all_markets)

    # Call the utility to import all events with duplicate check
    event_import_with_duplicate_check(all_markets, cur)

    # Call the utility to import all lines
    lines_import_without_check(all_lines, cur)

    # Call the import for all alternative event markets
    alternate_import(all_event_ids, cur)

    # Commit all database changes for data import and alternative import
    connection.commit()
