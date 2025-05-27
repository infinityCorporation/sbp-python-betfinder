# Library imports
import uuid
from datetime import datetime, timezone
import json
import os

# Script imports
from scripts.dbmanager import check_bet_time_v2, check_bet_time_v3
from scripts.alternate_import import alternate_import
from scripts.utilities import event_import_with_duplicate_check, lines_import_without_check, create_api_connection

# frisbiecorp@gmail.com: 5ab51a74ab7fea2414dbade0cf9d7229
# contact@arrayassistant.ai: 098b369ca52dc641b2bea6c901c24887
# efrisbie2232@gmail.com: cc1dcf7f444d59f7e4940113969b8e19

apiKey = "5ab51a74ab7fea2414dbade0cf9d7229"
conn = create_api_connection()

# Add the sports and market arrays
# sports = ['americanfootball_nfl', 'americanfootball_ncaaf', 'basketball_nba', 'basketball_ncaab', 'baseball_mlb',
#         'mma_mixed_martial_arts']
sports = ['basketball_nba', 'basketball_ncaab', 'baseball_mlb', 'americanfootball_nfl', 'americanfootball_ncaaf']
betting_markets = ['h2h', 'spreads', 'totals']

current_utc_time = datetime.now(timezone.utc)
date_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')

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
    check_bet_time_v3(cursor, "lines_data")
    check_bet_time_v3(cursor, "all_data")


def games_loop_call(parsed_url, bet_key):
    """
    This function takes in the raw data from the API, but doesn't actually pull it, and sorts it into an array that can
    actually be used in the program.
    :param parsed_url:
    :param bet_key:
    :return:
    """

    # I think that the issue is that you are calling 3 api endpoints for each type of betting line, therefore,
    # you are going to triple the number of duplicates

    # Loop through all returned json event objects for a given sport
    # (a) is an event here
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
            if not all_event_ids.__contains__({
                'id': a['id'],
                'key': a['sport_key'],
            }):
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
                        'team_one': a['home_team'],
                        'team_two': a['away_team'],
                        'event': event,
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
                'bet_key': bet_key,
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
            url = f"/v4/sports/{s}/odds/?regions=us&oddsFormat=american&markets={m}&apiKey={apiKey}"
            conn.request("GET", url)
            response = conn.getresponse()

            # requests.Response object; to read content:
            content = response.content
            parsed = response.json()

#            file_path = f"./scripts/data_store/{s}"
#            with open(file_path, "w") as file:
#                file.write(str(parsed))

            # print(parsed)

            games_loop_call(parsed, m)

            print("all_markets Array: ", all_markets)

    # Call the utility to import all events with duplicate check
    event_import_with_duplicate_check(all_markets, cur)

    # Call the utility to import all lines
    lines_import_without_check(all_lines, cur)

    # Call the import for all alternative event markets - Not always needed
    # alternate_import(all_event_ids, cur)

    # Commit all database changes for data import and alternative import
    connection.commit()
