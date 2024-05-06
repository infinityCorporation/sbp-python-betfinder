# This is the third positive EV and implementing the second method for finding positive EV bets.

# The concept is simple, I will use the average line set by the market to determine what lines actually present a
# positive expected value. By comparing each line to the average, it should be easy to find out whether there's an
# opportunity available. With more data, I can consider finding a weighted average based on sharper books like pinnacle.

import uuid
import numpy as np
from scripts.utilities import pull_event_lines, compare_lines

# First, grab all the lines of a given event and store them in an array that allows all of them to be accessed for that
# specific event


def line_manager(cur):
    """
    This new version of the line manager attempts to get all the lines of an event into two arrays within an event
    object
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

                # Create both a pair of arrays to remove both the vig and the total pos and neg arrays
                # Actually, first put it into the pair arrays, remove the vig from each pos and neg line, and then
                # add those to the total pos and neg arrays

                positive_line, negative_line = compare_lines(returned_line[3][0][0], returned_line[3][0][1])

                pair_array.append({
                    'uid': returned_line[0],
                    'book': returned_line[5],
                    'positive_line': positive_line,
                    'negative_line': negative_line,
                })

            # This is not in reference of returned line
            if len(pair_array) > 0:
                total_array.append({
                    "event_uid": event[0],
                    "event": event[1],
                    "commence_time": event[2],
                    "sport": event[7],
                    "home_team": home_team,
                    "away_team": away_team,
                    "pair_array": pair_array,
                    "positive_array": None,
                    "negative_array": None,
                    "average_positive": None,
                    "average_negative": None,
                })

    return total_array

# Next, attach the implied probabilities and all the given vig removed probabilities to the same array, or in a new one
# that is attached to the same array.


def probability_vig_processor(event):
    """
    Given an event, take its lines and find the implied probability, then remove the vig, then return the event with a
    new positive and negative array instead of a pair array
    :param event:
    :return event:
    """

    positive_array = []
    negative_array = []

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

    def calculate_two_way_vig(negative_probability, positive_probability):
        """
        This is the new version of calculating the no vig odds and returning the juice.
        :param negative_probability:
        :param positive_probability:
        :return vig, new_positive_price, new_negative_price:
        """
        print("positive prob: ", positive_probability, " negative prob: ", negative_probability)
        total_implied = np.abs(negative_probability) + np.abs(positive_probability)

        vig = (1 - ((1 / total_implied) * 100)) * 100
        new_positive_probability = (positive_probability / total_implied) * 100
        new_negative_probability = (negative_probability / total_implied) * 100

        return round(vig, 2), round(new_negative_probability, 2), round(new_positive_probability, 2)

    for outcome in event['pair_array']:
        outcome['positive_line']['probability'] = calculate_probability(outcome['positive_line']['price'])
        outcome['negative_line']['probability'] = calculate_probability(outcome['negative_line']['price'])

        vig, outcome['positive_line']['no_vig_price'], outcome['negative_line']['no_vig_price'] = calculate_two_way_vig(
            outcome['positive_line']['probability'], outcome['negative_line']['probability'])

        positive_array.append(outcome['positive_line'])
        negative_array.append(outcome['negative_line'])

    event['positive_array'], event['negative_array'] = positive_array, negative_array

    return event


# Next, calculate the average line for both sides of the event, and save it in the events array.


def average_processor(event):
    """
    Given an event with a positive and negative array of lines, find the vig-removed market average of those lines and
    put it in the event object
    :param event:
    :return event:
    """

    average_positive = 0
    average_negative = 0

    for line in event['positive_array']:
        average_positive += line['price']

    average_positive = average_positive / len(event['positive_array'])

    for line in event['negative_array']:
        average_negative += line['price']

    average_negative = average_negative / len(event['negative_array'])

    event['average_positive'] = average_positive
    event['average_negative'] = average_negative

    return event


# Loop through and compare each line to the corresponding opposite average line.


def pev_main_loop(events):
    """
    This is the main functionality loop for the updated pev method, slightly longer than the previous main loop
    :param events:
    :return:
    """

    # First, take the lines from the lines manager and loop through to remove the vig from each one
    for event in events:
        event = probability_vig_processor(event)
        event = average_processor(event)

    # Now that we have hit the mid-point of finding the averages, this feels like a good place to stop. Test this and
    # make sure that you are actually getting average values out before continuing. There is a lot of weird stuff with
    # how the arrays are stacked, so I get the creeping feeling that there may be some issues there with that.

    # Now go through each event and find the average positive and negative line value

# Finally, check to see which lines have a positive expected value from any of the lines.


def ev_main(cursor, connection):
    """
    This is the main file function that manages the interaction with the server file as well as the database connections
    :param cursor:
    :param connection:
    :return:
    """

    # First, call the line manager to get the events and sort the lines
    event_array = line_manager(cursor)

    # Next, call the main loop to complete the functionality
    pev_main_loop(event_array)


    return

