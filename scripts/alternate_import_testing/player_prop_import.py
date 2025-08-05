from datetime import datetime, timezone
from scripts.alternate_import import betting_markets
from scripts.dbmanager import clear_bet_table
from scripts.utilities import create_api_connection
from ..utilities import player_event_import_v1, player_lines_import_v1
import uuid
from psycopg2.extras import execute_values
import json

# 100k key frisbiecorp@gmail.com: 3016e10212283b7a71a72dc824bacb34 - Cancelled
# 5M key frisbiecorp@gmail.com: 050d89b464607afacc0f6f6e1d3c55d3

apiKey = "050d89b464607afacc0f6f6e1d3c55d3"
conn = create_api_connection()

# Add the sports and market arrays
sports = ['icehockey_nhl', 'basketball_nba', 'basketball_wnba', 'basketball_ncaab', 'baseball_mlb',
          'americanfootball_nfl', 'mma_mixed_martial_arts', 'americanfootball_ncaaf', 'icehockey_ahl']
betting_markets = ['h2h']
regions = ["us", "us2"]

current_utc_time = datetime.now(timezone.utc)
date_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')

# Initialize the necessary arrays
all_markets = []
all_lines = []
all_event_ids = []

# First, get all the events from the all_data table (Can also have these passed in from the data import)
baseball_props = ("batter_home_runs,batter_hits,batter_total_bases,batter_rbis,batter_runs_scored,"
              "batter_hits_runs_rbis,batter_singles,batter_doubles,batter_triples,batter_walks,"
              "batter_strikeouts,batter_stolen_bases,pitcher_strikeouts,pitcher_hits_allowed,"
              "pitcher_walks,pitcher_earned_runs,pitcher_outs")

football_props = ("player_assists,player_defensive_interceptions,player_field_goals,player_kicking_points,"
             "player_pass_attempts,player_pass_completions,player_pass_interceptions,player_pass_longest_completion,"
             "player_pass_rush_reception_tds,player_pass_rush_reception_yds,player_pass_tds,player_pass_yds,"
             "player_pass_yds_q1,player_pats,player_receptions,player_reception_longest,player_reception_tds,"
             "player_reception_yds,player_rush_attempts,player_rush_longest,player_rush_reception_tds,"
             "player_rush_reception_yds,player_rush_tds,player_rush_yds,player_sacks,player_solo_tackles,"
             "player_tackles_assists")

basketball_props = ("player_points,player_points_q1,player_rebounds,player_rebounds_q1,player_assists,player_assists_q1,"
             "player_threes,player_blocks,player_steals,player_blocks_steals,player_turnovers,"
             "player_points_rebounds_assists,player_points_rebounds,player_points_assists,player_rebounds_assists,"
             "player_field_goals,player_frees_made,player_frees_attempts")

hockey_props = ("player_points,player_power_play_points,player_assists,player_blocked_shots,player_shots_on_goal,"
             "player_goals,player_total_saves")


supported_props = {
    'baseball_mlb': baseball_props,
    'americanfootball_nfl': football_props,
    'americanfootball_ncaaf': football_props,
    'basketball_nba': basketball_props,
    'basketball_wnba': basketball_props,
    'basketball_ncaab': basketball_props,
    'icehockey_nhl': hockey_props,
    'icehockey_ahl': hockey_props,
}

player_events = []
player_lines = []

player_events_for_processing = []


def games_loop_call(parsed_url, bet_key):
    """
    Sorts API event data into structured event and line objects for internal processing.
    :param parsed_url: Parsed JSON data from API.
    :param bet_key: Identifier for bet type (e.g., spreads, totals, h2h).
    """
    for event_data in parsed_url:
        print(event_data)
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


def player_props_loop_call(parsed_url, bet_key):
    """
    Sorts API event data into structured event and line objects for internal processing.
    :param parsed_url: Parsed JSON data from API.
    :param bet_key: Identifier for bet type (e.g., spreads, totals, h2h).
    """
    for event_data in parsed_url:

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
            full_markets = []

            # Process each bookmaker
            for bookmaker in event_data["bookmakers"]:
                book = bookmaker['key']
                book_title = bookmaker['title']
                line_uid = str(uuid.uuid4())

                lines_per_book = []

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
                    player_lines.append(line_object)
                    lines_per_book.append(line_object)

                # Associate this bookmaker’s lines
                markets.append({
                    'book': book,
                    'title': book_title,
                    'lines': line_uid,
                })

                full_markets.append({
                    'book': book,
                    'title': book_title,
                    'lines': lines_per_book
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
                player_events.append({
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

                player_events_for_processing.append({
                    'uid': uid,
                    'event_uid': event_id,
                    'event': event_name,
                    'commence_time': commence_time,
                    'update_time': update_time,
                    'home_team': home_team,
                    'away_team': away_team,
                    'sport_key': sport_key,
                    'sport_name': sport_name,
                    'markets': full_markets,
                    'bet_key': bet_key,
                })

        except (NameError, TypeError) as e:
            print("Error while processing event:")
            print(json.dumps(event_data, indent=2))
            print(f"Exception: {e}")


def calculate_arbitrage(odds1, odds2):
    """
    Calculates arbitrage opportunity between two American odds.

    :param odds1: First line (can be positive or negative)
    :param odds2: Second line (can be positive or negative)
    :return: (arbitrage_percentage, is_arbitrage)
    """

    def to_decimal(odds):
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1

    dec1 = to_decimal(odds1)
    dec2 = to_decimal(odds2)

    inv1 = 1 / dec1
    inv2 = 1 / dec2

    total_inverse = inv1 + inv2
    arbitrage_percentage = (1 - total_inverse) * 100
    is_arbitrage = total_inverse < 1

    return round(arbitrage_percentage, 4), is_arbitrage


def calculate_arbitrage_stake(positive_odds, negative_odds):
    """
    This function calculates the stake that should be applied to line A and line B
    :param positive_odds:
    :param negative_odds:
    :return:
    """

    positive_odds = (positive_odds / 100) + 1
    negative_odds = (100 / (-negative_odds)) + 1

    if negative_odds == 0:
        return 1

    stake_b = positive_odds / negative_odds

    return stake_b


def arbitrage_bulk_insert(complete_arbitrage_table, cur):
    """
    Bulk insert arbitrage opportunities into the arbitrage_data table using execute_values.
    """
    sql = """
    INSERT INTO arbitrage_data (
        uid, event_uid, event, home_team, away_team, commence_time,
        sport, positive_play_price, positive_play_name, positive_play_book, positive_play_stake,
        negative_play_price, negative_play_name, negative_play_book, negative_play_stake,
        arbitrage_percentage, bet_type
    ) VALUES %s
    """

    values = [
        (
            row['uid'],
            row['event_uid'],
            row['game'],  # 'game' is mapped to 'event' in table
            row['home_team'],
            row['away_team'],
            row['commence_time'],
            row['sport'],
            row['positive_play_price'],
            row['positive_play_name'],
            row['positive_play_book'],
            row['positive_play_stake'],
            row['negative_play_price'],
            row['negative_play_name'],
            row['negative_play_book'],
            row['negative_play_stake'],
            row['arb_percent'],
            row['bet_type'],
        )
        for row in complete_arbitrage_table
    ]

    execute_values(cur, sql, values)
    print(f"{len(values)} arbitrage records inserted.")


def format_snake_case_label(snake_str):
    """
    Converts a snake_case string to a human-readable, capitalized string.
    Example: "batter_hits_runs_rbis" -> "Batter Hits Runs Rbis"
    """
    return ' '.join(word.capitalize() for word in snake_str.split('_'))


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
        for m in betting_markets:
            parsed_array = []

            for r in regions:
                url = f"/v4/sports/{s}/odds/?regions={r}&oddsFormat=american&markets={m}&apiKey={apiKey}"
                conn.request("GET", url)

                response = conn.getresponse()
                parsed = response.json()
                for x in parsed:
                    parsed_array.append(x)
                print(r, " ", len(parsed_array))

            games_loop_call(parsed_array, m)

    player_prop_main(all_markets, cur)

    # Commit all database changes for data import and alternative import
    connection.commit()


def player_prop_main(event_array, cursor):
    """
    The main player prop function intended to ingest and find arb/pev opportunities within the player props
    :param cursor:
    :param event_array:
    :return:
    """

    print("player prop main is running")
    for e in event_array:
        sport_key = e['sport_key']
        valid_markets = supported_props.get(sport_key)

        parsed_array = []

        if valid_markets:

            url = (f"/v4/sports/{e['sport_key']}/events/{e['event_uid']}/odds/?regions=us"
                   f"&oddsFormat=american&markets={valid_markets}&apiKey={apiKey}")
            conn.request("GET", url)

            response = conn.getresponse()
            parsed = response.json()

            parsed_array.append(parsed)
        player_props_loop_call(parsed_array, "player_props")

    clear_bet_table(cursor, "player_prop_data")
    clear_bet_table(cursor, "player_prop_lines_data")

    player_event_import_v1(player_events, cursor)
    player_lines_import_v1(player_lines, cursor)

    arb_match_count = 0
    middling_match_count = 0
    compare_match_count = 0

    arbitrage_object_collection = []

    try:
        for event in player_events_for_processing:
            over_lines = []
            under_lines = []
            event_iteration_count = 0

            for market in event['markets']:
                for line in market['lines']:
                    for outcome in line['outcomes']:
                        if outcome['name'] == "Over":
                            if outcome not in over_lines:
                                over_lines.append({
                                    "book": line['book'],
                                    "prop": line['key'],
                                    "name": outcome['name'],
                                    "description": outcome['description'],
                                    "price": outcome['price'],
                                    "point": outcome['point'],
                                })
                        else:
                            if outcome not in under_lines:
                                under_lines.append({
                                "book": line['book'],
                                "prop": line['key'],
                                "name": outcome['name'],
                                "description": outcome['description'],
                                "price": outcome['price'],
                                "point": outcome['point'],
                            })

            for over in over_lines:
                for under in under_lines:
                    event_iteration_count += 1
                    if (over['book'] is not under['book'] and over['prop'] == under['prop']
                            and over['description'] == under['description']):
                        if over['point'] <= under['point']:
                            if over['point'] < under['point']:
                                middling_match_count += 1
                            compare_match_count += 1
                            arb_percent, is_arb = calculate_arbitrage(over['price'], under['price'])

                            if is_arb:
                                arb_match_count += 1
                                print("calculated arb percentage: ", arb_percent, " from ", over['price'], " - ",
                                      under['price'])
                                print("Arb found: arb percentage = ", arb_percent)
                                print("Arb play: ", over, " and ", under)

                                if (over['price'] > under['price']):
                                    stake_b = calculate_arbitrage_stake(over['price'], under['price'])

                                    arb_table_object = {
                                        "uid": str(uuid.uuid4()),
                                        "event_uid": event['uid'],
                                        "game": event['event'],
                                        "commence_time": event['commence_time'],
                                        "home_team": event['home_team'],
                                        "away_team": event['away_team'],
                                        "sport": event['sport_name'],
                                        "bet_type": format_snake_case_label(over['prop']),
                                        "positive_play_price": over['price'],
                                        "positive_play_name": f"{over['description']} - {over['name']} {over['point']}",
                                        "positive_play_book": over['book'],
                                        "positive_play_stake": 1,
                                        "negative_play_price": under['price'],
                                        "negative_play_name": f"{under['description']} - {under['name']} {under['point']}",
                                        "negative_play_book": under['book'],
                                        "negative_play_stake": stake_b,
                                        "arb_percent": arb_percent,
                                    }
                                    arbitrage_object_collection.append(arb_table_object)

                                else:
                                    stake_b = calculate_arbitrage_stake(under['price'], over['price'])

                                    arb_table_object = {
                                        "uid": str(uuid.uuid4()),
                                        "event_uid": event['uid'],
                                        "game": event['event'],
                                        "commence_time": event['commence_time'],
                                        "home_team": event['home_team'],
                                        "away_team": event['away_team'],
                                        "sport": event['sport_name'],
                                        "bet_type": format_snake_case_label(over['prop']),
                                        "positive_play_price": under['price'],
                                        "positive_play_name": f"{under['description']} - {under['name']} {under['point']}",
                                        "positive_play_book": under['book'],
                                        "positive_play_stake": 1,
                                        "negative_play_price": over['price'],
                                        "negative_play_name": f"{over['description']} - {over['name']} {over['point']}",
                                        "negative_play_book": over['book'],
                                        "negative_play_stake": stake_b,
                                        "arb_percent": arb_percent,
                                    }
                                    arbitrage_object_collection.append(arb_table_object)
    except Exception:
        print("Something went wrong")
        print(Exception.with_traceback())

    arbitrage_bulk_insert(arbitrage_object_collection, cursor)


    print("Arb count: ", arb_match_count)
    print("Middling count: ", middling_match_count)
