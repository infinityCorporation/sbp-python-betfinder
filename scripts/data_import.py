# Library imports
import uuid
from datetime import datetime, timezone
import json

from scripts.alternate_import import betting_markets
from scripts.arbitrage import arbitrage_main
from scripts.dbmanager import clear_bet_table
from scripts.pev2 import ev_main
from scripts.utilities import event_import_v2, lines_import_v2, create_api_connection

# frisbiecorp@gmail.com: 5ab51a74ab7fea2414dbade0cf9d7229
# contact@arrayassistant.ai: 098b369ca52dc641b2bea6c901c24887
# efrisbie2232@gmail.com: cc1dcf7f444d59f7e4940113969b8e19

# pro key frisbiecorp@gmail.com: c95efda5321b24d2bbb587407b6d0012
# 100k key frisbiecorp@gmail.com: 3016e10212283b7a71a72dc824bacb34

apiKey = "3016e10212283b7a71a72dc824bacb34"
conn = create_api_connection()

# Add the sports and market arrays
sports = ['icehockey_nhl', 'basketball_nba', 'basketball_wnba', 'basketball_ncaab', 'baseball_mlb',
          'americanfootball_nfl', 'mma_mixed_martial_arts', 'americanfootball_ncaaf', 'icehockey_ahl']
default_markets = {'h2h', 'totals', 'spreads'}
betting_markets = ['h2h', 'totals', 'spreads']
regions = ["us", "us2"]

supported_markets = {
    'mma_mixed_martial_arts': {'h2h'},
    # 'boxing_boxing': {'h2h'},
    # Other sports default to all markets unless specified
}

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


def clean_up_prep(cursor):
    """
    This functions purpose is to clean up the database and prep it for another data pull. The idea is to clear any
    events that have ended, been cancelled, or duplicates.
    :param cursor:
    :return:
    """

    # Delete all
    clear_bet_table(cursor, "lines_data")
    clear_bet_table(cursor, "all_data")


def games_loop_call(parsed_url, bet_key):
    """
    Sorts API event data into structured event and line objects for internal processing.
    :param parsed_url: Parsed JSON data from API.
    :param bet_key: Identifier for bet type (e.g., spreads, totals, h2h).
    """
    for event_data in parsed_url:
        print("working on", event_data)

        try:
            uid = str(uuid.uuid4())
            event_id = event_data['id']
            home_team = event_data['home_team']
            away_team = event_data['away_team']
            commence_time = event_data['commence_time']
            event_name = f"{home_team} vs {away_team}"
            sport_key = event_data['sport_key']
            sport_name = event_data['sport_title']
            update_time = date_time
            markets = []

            # Process each bookmaker
            for bookmaker in event_data["bookmakers"]:
                book = bookmaker['key']
                book_title = bookmaker['title']
                line_uid = str(uuid.uuid4())

                # Process each market under this bookmaker
                for market in bookmaker['markets']:
                    line_object = {
                        'uid': line_uid,
                        'key': market['key'],
                        'last_update': market['last_update'],
                        'commence_time': commence_time,
                        'outcomes': market['outcomes'],
                        'book': book,
                        'team_one': home_team,
                        'team_two': away_team,
                        'event': event_name,
                        'event_uid': event_data['id'],
                    }
                    all_lines.append(line_object)

                # Associate this bookmaker’s lines
                markets.append({
                    'book': book,
                    'title': book_title,
                    'lines': line_uid,
                })

            # Check for existing event to merge markets
            existing_event = next((
                e for e in all_markets
                if e['home_team'] == home_team and
                   e['away_team'] == away_team and
                   e['commence_time'] == commence_time and
                   e['bet_key'] == bet_key
            ), None)

            if existing_event:
                existing_event['markets'].extend(markets)
            else:
                all_markets.append({
                    'uid': uid,
                    'event_uid': event_id,
                    'event': event_name,
                    'commence_time': commence_time,
                    'update_time': update_time,
                    'home_team': home_team,
                    'away_team': away_team,
                    'sport_key': sport_key,
                    'sport_name': sport_name,
                    'markets': markets,
                    'bet_key': bet_key,
                })

        except (NameError, TypeError) as e:
            print("Error while processing event:")
            print(json.dumps(event_data, indent=2))
            print(f"Exception: {e}")


def get_data(connection, cur):
    """
    This function actually makes the http calls to the API to get the data. It first calls a database clean up, then
    calls the data, then passes it to games_loop_call to format, then it checks each event in the all_market array for
    duplicates, then it deletes duplicate events and lines, then it adds the event to the database table.
    :param connection:
    :param cur:
    :return:
    """

    connection.commit()

    # This grabs all the lines from the api and pushes them to the all_markets array
    for s in sports:
        valid_markets = supported_markets.get(s, default_markets)

        for m in betting_markets:
            parsed_array = []

            if m not in valid_markets:
                continue

            for r in regions:
                url = f"/v4/sports/{s}/odds/?regions={r}&oddsFormat=american&markets={m}&apiKey={apiKey}"
                conn.request("GET", url)

                response = conn.getresponse()
                parsed = response.json()
                for x in parsed:
                    parsed_array.append(x)
                print(r, " ", len(parsed_array))

            games_loop_call(parsed_array, m)

    # Clean up just before import, not when the program starts
    clean_up_prep(cur)

    # Call the utility to import all events with duplicate check
    event_import_v2(all_markets, cur)

    # Call the utility to import all lines
    lines_import_v2(all_lines, cur)

    arbitrage_main(connection, cur, all_markets, all_lines)
    ev_main(connection, cur, all_markets, all_lines)

    # Call the import for all alternative event markets - Not always needed
    # alternate_import(all_event_ids, cur)

    # Commit all database changes for data import and alternative import
    connection.commit()
