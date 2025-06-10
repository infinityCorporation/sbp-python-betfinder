# Library imports
import http.client as client
import uuid
from datetime import datetime, timezone
import json

# Utility imports
from scripts.utilities import create_api_connection


# Initialize arrays for alternative market keys
# betting_markets = ['h2h_q1']
# betting_markets = ['h2h_q1', 'h2h_q2', 'h2h_q3', 'h2h_q4']
betting_markets = ['h2h_q1', 'h2h_q2', 'h2h_q3', 'h2h_q4', 'h2h_h1', 'h2h_h2', 'spreads_q1', 'spreads_q2',
                   'spreads_q3', 'spreads_q4', 'spreads_h1', 'spreads_h2', 'totals_q1', 'totals_q2', 'totals_q3',
                   'totals_q4', 'totals_h1', 'totals_h2', ]

# Create an HTTPS connection for the data API
apiKey = "cc1dcf7f444d59f7e4940113969b8e19"
conn = create_api_connection()

# Set up a date-time variable to create time stamps
current_utc_time = datetime.now(timezone.utc)
date_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')

# Initialize all the necessary Arrays
all_alt_lines = []
all_alt_markets = []


def get_event_id():
    return


def games_loop_call(parsed, bet_key):
    """
    This function takes in the raw data from the API, but doesn't actually pull it, and sorts it into an array that can
    actually be used in the program.
    :param parsed:
    :param bet_key:
    :return:
    """

    print("The games loop got: ", parsed)

    try:
        uid = str(uuid.uuid4())
        event_id = parsed['id']
        event = parsed['home_team'] + " vs " + parsed['away_team']
        commence_time = parsed['commence_time']
        update_time = date_time
        home_team = parsed['home_team']
        away_team = parsed['away_team']
        sport_key = parsed['sport_key']
        sport_name = parsed['sport_title']
        event_markets = []

        # Parse though all the books in the events betting options
        for book in parsed["bookmakers"]:
            id_creator = str(uuid.uuid4())

            lines_uid = id_creator
            book_key = book['key']
            book_title = book['title']

            # Parse through all the lines in each book's markets
            for line in book['markets']:

                line_uid = id_creator
                line_key = line['key']
                last_update = line['last_update']
                outcomes = line['outcomes']

                # Line object just for the given bookmaker
                line_object = {
                    'uid': line_uid,
                    'key': line_key,
                    'last_update': last_update,
                    'commence_time': commence_time,
                    'outcomes': outcomes,
                    'book': book_key,
                    'team_one': parsed['home_team'],
                    'team_two': parsed['away_team']
                }
                all_alt_lines.append(line_object)

            # All information about a single bookmaker
            bookmaker_object = {
                'book': book_key,
                'title': book_title,
                'lines': lines_uid,
            }

            print("The bookmaker Object is: ", bookmaker_object)

            event_markets.append(bookmaker_object)

        # Full object for the given event
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
            'markets': event_markets,
            'bet_key': bet_key,
        }

        print(event_object)
        all_alt_markets.append(event_object)

    except NameError:
        print("The line with the error was: ")
        print(json.dumps(parsed))
    except TypeError:
        print("There was a type err here: ")
        print(json.dumps(parsed))


def alternate_import(event_ids, cur):
    """
    Given an event id and the type of sport, get all the necessary lines and add them to the lines_data
    table. Specify in name the type of betting line that you are processing.
    :param event_ids:
    :param cur:
    :return:
    """

    print("Events passed were: ", event_ids)

    # For each event, loop through all provided markets (remember that depending on the event and sport key, we may have
    # different markets for you will need a way to check for that)
    for event in event_ids:
        for m in betting_markets:
            url = ("/v4/sports/" + event['key'] + "/events/" + event['id'] +
                   "/odds/?regions=us&oddsFormat=american&markets=" + m + "&apiKey=" + apiKey)

            conn.request("GET", url)

            print("This is getting an alternative line...")

            response = conn.getresponse()
            content = response.read()
            parsed = json.loads(content)

            games_loop_call(parsed, m)

            print(parsed)

    # Call the utility to check for duplicates and then import the event into all_data
    event_import_with_duplicate_check(all_alt_markets, cur)

    # Call the utility to import all given lines
    lines_import_without_check(all_alt_lines, cur)
