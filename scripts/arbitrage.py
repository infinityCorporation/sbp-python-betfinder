from scripts.utilities import pull_event_lines
import uuid
from psycopg2.extras import execute_values


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
                if returned_line['key'] == 'h2h':
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
                else:
                    for outcome in returned_line['outcomes']:
                        if outcome['price'] > 0:
                            positive_array.append({
                                'uid': returned_line['uid'],
                                'name': outcome['name'],
                                'price': outcome['price'],
                                'point': outcome['point'],
                                'book': returned_line['book'],
                            })
                        elif outcome['price'] < 0:
                            negative_array.append({
                                'uid': returned_line['uid'],
                                'name': outcome['name'],
                                'price': outcome['price'],
                                'point': outcome['point'],
                                'book': returned_line['book'],
                            })


        total_array.append({
            "event_uid": event['uid'],
            "key": event['bet_key'],
            "positive_lines": positive_array,
            "negative_lines": negative_array,
        })

    for event in total_array:
        print(event['event_uid'], " : ", event['positive_lines'], " : ", event['negative_lines'])

    return total_array


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

    stake_b = positive_odds / negative_odds

    return stake_b


def arbitrage_loop(total_array):
    """
    The purpose of this function is to bring together the arrays from the lines manager as well as the calculations
    from the arbitrage calculator. Will return an array of available arbitrage plays.
    :param total_array:
    :return arbitrage_plays:
    """

    arbitrage_plays = []

    for event in total_array:
        positive_arr = event['positive_lines']
        negative_arr = event['negative_lines']

        if len(positive_arr) > 0:
            for p in positive_arr:
                for n in negative_arr:

                    percentage, is_arb = calculate_arbitrage(p['price'], n['price'])

                    if event['key'] == 'h2h':
                        if is_arb and p['name'] != n['name']:
                            print("Positive Percentage: ", percentage)
                            arbitrage_plays.append({
                                "event_uid": event['event_uid'],
                                "positive": p,
                                "negative": n,
                                "play_percentage": percentage,
                            })
                    else:
                        if is_arb and p['name'] != n['name'] and abs(p['point']) != abs(n['point']):
                            print("Point mismatch found: ", p['point'], " - ", n['point'])
                        if is_arb and p['name'] != n['name'] and abs(p['point']) == abs(n['point']):
                            print("Positive Percentage: ", percentage)
                            arbitrage_plays.append({
                                "event_uid": event['event_uid'],
                                "positive": p,
                                "negative": n,
                                "play_percentage": percentage,
                            })

    return arbitrage_plays


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



def create_final_table(plays, cur):
    """
    Given the array of plays with the associated UIDs
    :param plays:
    :param cur:
    :return:
    """

    # Clear all the old plays
    arbitrage_table_delete_sql = "DELETE FROM arbitrage_data"
    cur.execute(arbitrage_table_delete_sql)

    complete_arbitrage_table = []

    for play in plays:
        uid_search_sql = "SELECT * FROM all_data WHERE uid = %s"
        cur.execute(uid_search_sql, (play['event_uid'],))

        result = cur.fetchone()
        uid = str(uuid.uuid4())

        negative_stake = calculate_arbitrage_stake(play['positive']['price'], play['negative']['price'])

        complete_arbitrage_table.append({
            "uid": uid,
            "event_uid": result[0],
            "game": result[1],
            "commence_time": result[2],
            "home_team": result[4],
            "away_team": result[5],
            "sport": result[7],
            "bet_type": result[9],
            "positive_play_price": play['positive']['price'],
            "positive_play_name": play['positive']['name'],
            "positive_play_book": play['positive']['book'],
            "positive_play_stake": 1,
            "negative_play_price": play['negative']['price'],
            "negative_play_name": play['negative']['name'],
            "negative_play_book": play['negative']['book'],
            "negative_play_stake": negative_stake,
            "arb_percent": play['play_percentage']
        })

    complete_arbitrage_table.sort(key=lambda x: x['arb_percent'], reverse=True)

    arbitrage_bulk_insert(complete_arbitrage_table, cur)


def arbitrage_main(connection, cursor, all_markets, all_lines):
    """
    This is the main function that pulls together the calculations and data management aspects of the arbitrage
    calculator
    :param connection:
    :param cursor:
    :param all_markets:
    :param all_lines:
    :return:
    """

    total = line_manager(all_markets, all_lines)
    all_plays = arbitrage_loop(total)
    create_final_table(all_plays, cursor)

    connection.commit()
