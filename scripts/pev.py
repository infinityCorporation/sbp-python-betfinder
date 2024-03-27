# The aim of this file is to transfer all the core positive EV calculation while also adding a new database line
# storage system

import uuid
import numpy as np
from scripts.utilities import pull_event_lines

# It looks like the general layout is -> calculate odds -> calculate profit -> calculate expected value -> package
# results -> send to table.
# NOTE: For positive EV the lines have to be in the same book


def line_manager(cur):
    """
    This is essentially a function meant to pull an event, or two in this case, and then get their lines such that they
    can be compared.
    :param cur:
    :return:
    """

    total_array = []

    pull_all_sql = "SELECT * FROM all_data"
    cur.execute(pull_all_sql)

    all_array = cur.fetchall()

    # New plan, we are now creating an array of arrays. The uid of the event and all the line UIDs

    # The issue found is that there are numerous lines, specifically over/under ones where both sides are negative
    # For arbitrage, this mistake persists, two negative lines will never have an arbitrage play but two positive lines
    # could, and you don't want to miss out on those because they would be huge

    for event in all_array:

        pair_array = []

        home_team = event[4]
        away_team = event[5]

        lines = pull_event_lines(event)

        print("The current event is: " + event[1])

        for line in lines:

            positive_line = {}
            negative_line = {}

            search_lines_sql = "SELECT * FROM lines_data WHERE uid = %s"
            cur.execute(search_lines_sql, (line,))

            returned_line = cur.fetchone()

            # Technically we already have both outcomes so really the only issue here is labelling. Here is an idea:
            # If both outcomes are negative, get rid of the line
            # If both are positive, add one to the positive line and one to the negative
            # Otherwise, just do things normally
            # Note that now the calculations for profit and probability need to be conditional

            # Since the returned line encompasses where the event is added, events are added even when there is no lines
            if returned_line:

                print("The current line is: " + returned_line[3][0][0]['name'])

                # There is a chance that neither of these options happen

                if returned_line[3][0][0]['price'] > 0 and returned_line[3][0][1]['price'] > 0:
                    positive_line = {
                        'name': returned_line[3][0][0]['name'],
                        'price': int(returned_line[3][0][0]['price'])
                    }
                    negative_line = {
                        'name': returned_line[3][0][1]['name'],
                        'price': int(returned_line[3][0][1]['price'])
                    }

                    pair_array.append({
                        'uid': returned_line[0],
                        'book': returned_line[5],
                        'positive_line': positive_line,
                        'negative_line': negative_line,
                    })

                elif not (returned_line[3][0][0]['price'] < 0 and returned_line[3][0][1]['price'] < 0):
                    for outcome in returned_line[3][0]:
                        if outcome['price'] > 0:
                            positive_line = {
                                'name': outcome['name'],
                                'price': int(outcome['price']),
                            }

                        elif outcome['price'] < 0:
                            negative_line = {
                                'name': outcome['name'],
                                'price': int(outcome['price']),
                            }

                    pair_array.append({
                        'uid': returned_line[0],
                        'book': returned_line[5],
                        'positive_line': positive_line,
                        'negative_line': negative_line,
                    })

            print("Current Pair Array Length: ", len(pair_array))
            if len(pair_array) > 0:
                print(pair_array[len(pair_array) - 1])

            # This is not in reference of returned line
            if len(pair_array) > 0:

            # This is the problem: There are multiple lines in paired_lines, you are treating it like one.
                total_array.append({
                    "event_uid": event[0],
                    "event": event[1],
                    "commence_time": event[2],
                    "sport": event[7],
                    "home_team": home_team,
                    "away_team": away_team,
                    "paired_lines": pair_array,
                })


    for event in total_array:
        for pair in event['paired_lines']:
            print(event['event_uid'], " : ", pair['positive_line'], " : ",
                  pair['negative_line'])

    return total_array


def calculate_probability(odds: int):
    """
    The goal here is to calculate the odds regardless of whether they are positive or negative.
    :param odds:
    :return:
    """
    if odds > 0:
        odds = np.abs(odds)
        return round(((100 / (odds + 100)) * 100), 2)
    elif odds < 0:
        odds = np.abs(odds)
        return round(((odds / (odds + 100)) * 100), 2)


def calculate_profits(odds):
    """
    This function is to calculate both the negative and positive odds.
    :param odds:
    :return:
    """
    if odds > 0:
        return round(((odds / 100) * 100), 2)
    elif odds < 0:
        return round(((100 / odds) * 100), 2)


# Here is where we are putting the Vig calculation and the EV calculation
def calculate_two_way_vig(negative_probability, positive_probability):
    """
    This is the new version of calculating the no vig odds and returning the juice.
    :param negative_probability:
    :param positive_probability:
    :return vig, new_positive_price, new_negative_price:
    """
    total_implied = np.abs(negative_probability) + np.abs(positive_probability)

    vig = (1 - ((1 / total_implied) * 100)) * 100
    new_positive_probability = (positive_probability / total_implied) * 100
    new_negative_probability = (negative_probability / total_implied) * 100

    return round(vig, 2), round(new_positive_probability, 2), round(new_negative_probability, 2)


def calculate_expected_value(winning_probability, implied_profit):
    """
    Given the winning and losing probability and the current bet price, return the expected value in
    percentage based terms.
    :param winning_probability:
    :param implied_profit:
    :return expected_value:
    """
    losing_probability = 100 - winning_probability
    expected_value = ((winning_probability / 100) * implied_profit) - losing_probability
    return round(expected_value, 2)


# The essential columns: pev uid, event_uid, event, home_team, away_team, commence_time, positive_play_price,
#                        positive_play_name, positive_play_percentage
def create_final_table(positive_ev_array, cur):
    """
    This function will insert all the processed data into a final table
    :param positive_ev_array:
    :param cur:
    :return:
    """
    uid = str(uuid.uuid4())

    for row in positive_ev_array:
        pev_insert_sql = ("INSERT INTO pev_data (uid, event_uid, event, home_team, away_team, commence_time, sport, "
                          "positive_play_price, positive_play_name, positive_play_percentage, book) VALUES (%s, %s, %s, %s, "
                          "%s, %s, %s, %s, %s, %s, %s)")
        cur.execute(pev_insert_sql, (uid, row['event']['event_uid'], row['event']['event'], row['event']['home_team'],
                                     row['event']['away_team'], row['event']['commence_time'], row['event']['sport'],
                                     row['line']['price'], row['line']['name'], row['positive_expected_value'],
                                     row['book']))

        # This may arguably be too heavily layered with JSON formatting. Maybe step it down in earlier functions


# Here you need a main loop function to pull everything together
# The main loop should contain data insertion into a new positive ev table (Delete the old one)
def pev_main_loop(total_array, cur):
    """
    This is the main loop that calls all the functions to pull, process, and place the data.
    :param total_array:
    :param cur:
    :return:
    """
    # Please fill in the params when they are known.
    expected_value_results = []

    for event in total_array:
        for line in event['paired_lines']:

            positive_line = line['positive_line']
            negative_line = line['negative_line']

            # Add in the opposing line to check if the program is actually calculating the correct values.
            # For future coding, here is where I imagine I can compound some of the billion utility functions
            if (positive_line['price'] != 0) and (negative_line['price'] != 0):
                positive_probability = calculate_probability(positive_line['price'])
                negative_probability = calculate_probability(negative_line['price'])

                positive_profit = calculate_profits(positive_line['price'])
                negative_profit = calculate_profits(negative_line['price'])

                # Here is where the expected value and vig calculations need to be done
                # Just to note: there is no actual reason to return the vig, it can just be calculated and then deleted
                event_vig, adjusted_positive_probability, adjusted_negative_probability = calculate_two_way_vig(
                    positive_probability, negative_probability)
                positive_expected_value = calculate_expected_value(adjusted_positive_probability, positive_profit)
                negative_expected_value = calculate_expected_value(adjusted_negative_probability, negative_profit)

                # Finally, append the results to a list that can be added to a table (still needs a function)
                if positive_expected_value > 0:
                    expected_value_results.append({
                        'event': event,
                        'book': str(line['book']),
                        'line': line['positive_line'],
                        'positive_expected_value': positive_expected_value,
                    })
                elif negative_expected_value > 0:
                    expected_value_results.append({
                        'event': event,
                        'book': str(line['book']),
                        'line': line['negative_line'],
                        'positive_expected_value': negative_expected_value
                    })

    # Create the final table
    create_final_table(expected_value_results, cur)


# This is the main function for the positive ev function
def positive_ev_main(connection, cursor):
    """
    This is the main loop for the positive EV tracker that
    :param connection:
    :param cursor:
    :return:
    """
    # Here, we will call the main loop then commit the connection

    # First, grab all the lines from the lines manager
    total_lines = line_manager(cursor)

    # Next, pass all the lines through the main loop
    pev_main_loop(total_lines, cursor)

    # Finally, commit the connection
    connection.commit()

