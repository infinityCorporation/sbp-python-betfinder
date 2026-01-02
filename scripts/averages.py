import uuid
from psycopg2.extras import execute_values, Json
from scripts.utilities import pull_event_lines
from datetime import datetime, timezone


def line_manager(all_markets, all_lines):
    """
    This is essentially a function meant to pull an event, or two in this case, and then get their lines such that they
    can be compared.
    :param all_markets:
    :param all_lines:
    :return:
    """

    total_array = []

    for event in all_markets:

        positive_array = []
        negative_array = []

        lines = pull_event_lines(event)

        for line in lines:

            returned_line = next((bet for bet in all_lines if bet['uid'] == line), None)

            if returned_line:
                for outcome in returned_line['outcomes']:
                    if outcome['price'] > 0:
                        positive_array.append({
                            'uid': returned_line['uid'],
                            'name': outcome['name'],
                            'price': outcome['price'],
                            'book': returned_line['book'],
                        })
                    elif outcome['price'] < 0:
                        negative_array.append({
                            'uid': returned_line['uid'],
                            'name': outcome['name'],
                            'price': outcome['price'],
                            'book': returned_line['book'],
                        })


        total_array.append({
            "event_uid": event['uid'],
            "key": event['bet_key'],
            "event_name": event['event'],
            "commence_time": event["commence_time"],
            "positive_lines": positive_array,
            "negative_lines": negative_array,
        })

    for event in total_array:
        print(event['event_uid'], " : ", event['positive_lines'], " : ", event['negative_lines'])

    return total_array


def calculate_averages(total):
    """
    Here we calculate the average for an event on a given update
    :param total:
    :return:
    """

    print(total[0])

    side_one_obj = {}
    side_two_obj = {}

    all_averages = []

    for event in total:
        side_one_avg = 0
        side_two_avg = 0

        if len(event['positive_lines']) > 0:
            for outcome in event['positive_lines']:
                side_one_avg += outcome['price']

            side_one_avg = side_one_avg / len(event['positive_lines'])

            event_time = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
            time_diff = event_time - datetime.now(timezone.utc)

            side_one_obj = {
                "team": event['positive_lines'][0]['name'],
                "key": event['key'],
                "event_name": event['event_name'],
                "commence_time": event['commence_time'],
                "avgs": {
                    "average_value": side_one_avg,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "time_till_event": time_diff.total_seconds(),
                }
            }

            all_averages.append(side_one_obj)

        if len(event['negative_lines']) > 0:
            for outcome in event['negative_lines']:
                side_two_avg += outcome['price']

            side_two_avg = side_two_avg / len(event['negative_lines'])

            event_time = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
            time_diff = event_time - datetime.now(timezone.utc)

            side_two_obj = {
                "team": event['negative_lines'][0]['name'],
                "key": event['key'],
                "event_name": event['event_name'],
                "commence_time": event['commence_time'],
                "avgs": {
                    "average_value": side_two_avg,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "time_till_event": time_diff.total_seconds(),
                }
            }

            all_averages.append(side_two_obj)

        print(side_one_obj)
        print(side_two_obj)

    return(all_averages)


def averages_bulk_import(averages, cur):
    """
    Now we bulk import all of the averages except we are not replacing we are just updating.
    :param averages:
    :param cur:
    :return:
    """
    sql = """
            INSERT INTO team_odds_change_data (
                team, "key", avgs, event, commence_time
            )
            VALUES %s
            ON CONFLICT (event, commence_time) DO UPDATE
            SET avgs = team_odds_change_data.avgs || EXCLUDED.avgs;
          """

    values = [
        (
            x['team'],
            x['key'],
            Json(x['avgs']),
            x['event_name'],
            x['commence_time'],
        )
        for x in averages
        if all(v is not None for v in (
            x['team'], x['key'], x['avgs'], x['event_name'], x['commence_time']
        ))
    ]

    execute_values(cur, sql, values)
    print(f"{len(values)} events added.")


def averages_main(all_markets, all_lines, cur):
    """
    The goal of this script is to calculate the average values over time for a given teams odds as we approach game
    time.
    :param all_markets:
    :param all_lines:
    :param cur:
    :return:
    """

    total_array = line_manager(all_markets, all_lines)

    averages = calculate_averages(total_array)

    averages_bulk_import(averages, cur)



