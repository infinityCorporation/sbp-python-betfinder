# This is the third positive EV and implementing the second method for finding positive EV bets.

# Classes are complete as of 5/23/24. Now the final goal is to two part. First, test the class functionality. Next,
# the goal is to create a system to compare the lines in each outcome against the opposing average and then pull the
# necessary details if it presents a positive EV opportunity.

# Library Imports
import uuid
import numpy as np
import json

# Method imports
from scripts.utilities import pull_event_lines, compare_lines

# Class Imports
from scripts.classes.eventClass import Event
from scripts.classes.outcomeClass import Outcome


# First, grab all the lines of a given event and store them in an array that allows all of them to be accessed for that
# specific event
def line_manager(cur, all_markets, all_lines):
    """
    This new version of the line manager attempts to get all the lines of an event into two arrays within an event
    object
    :param cur:
    :param all_markets:
    :param all_lines:
    :return:
    """

    total_array = []

    for event in all_markets:

        pair_array = []

        home_team = event['home_team']
        away_team = event['away_team']

        lines = pull_event_lines(event)

        for line in lines:
            search_lines_sql = "SELECT * FROM lines_data WHERE uid = %s"
            cur.execute(search_lines_sql, (line,))

            returned_line = cur.fetchone()

            if returned_line and returned_line is not None:
                positive_line, negative_line = compare_lines(returned_line[3][0][0], returned_line[3][0][1])
                outcome_object = Outcome(returned_line[0], returned_line[5], positive_line, positive_line.uid, negative_line,
                                         negative_line.uid, returned_line[1])
                pair_array.append(outcome_object)

        if len(pair_array) > 0:
            total_array.append(Event(event['uid'], event['event'], event['commence_time'], event['sport_name'], home_team, away_team, pair_array))

    return total_array


def pev_main_loop(events, cur):
    """
    This is the main functionality loop for the updated pev method, slightly longer than the previous main loop
    :param events:
    :param cur:
    :return:
    """
    total_pev_index = 0
    total_outcome_index = 0
    top_pev_index = 0

    # First, process the event. This process each outcome, the +/- arrays, and the averages
    for event in events:
        event.process_event()

        if len(event.positive_ev_outcomes) > 0:
            print("---------------------------------")
            print("Positive Expected Value Lines: ")
            for outcome in event.positive_ev_outcomes:
                print("---------------------------------")
                print(outcome.book, " | ", outcome.bet_type)
                if outcome.line_with_pev == outcome.negative_line:
                    print(outcome.line_with_pev.price, " | ", outcome.positive_line.price)
                    print(outcome.line_with_pev.probability, " | ", outcome.positive_line.probability)
                else:
                    print(outcome.line_with_pev.price, " | ", outcome.negative_line.price)
                    print(outcome.line_with_pev.probability, " | ", outcome.negative_line.probability)
                print("No Vig: ")
                print(outcome.line_with_pev.no_vig_price, " | ", outcome.line_with_pev.no_vig_probability)
                print("Percentage | ", outcome.positive_ev_percentage)
        else:
            print("No PEV Outcomes Found for ", event.event, "... ")

        print("Average no vig: ")
        if event.average_positive_h2h is not None:
            print(event.average_positive_h2h, " | ", event.average_negative_h2h)
        if event.average_positive_spreads is not None:
            print(event.average_positive_spreads, " | ", event.average_negative_spreads)
        if event.average_positive_totals is not None:
            print(event.average_positive_totals, " | ", event.average_negative_totals)

        total_pev_index += len(event.positive_ev_outcomes)
        print("PEV: ", total_pev_index)
        total_outcome_index += len(event.pair_array)
        print("TOTAL: ", total_outcome_index)
        top_pev_index += len(event.high_ev_outcomes)

        if len(event.positive_ev_outcomes) > 0:
            for outcome in event.positive_ev_outcomes:
                uid, event_uid = str(uuid.uuid4()), event.uid
                event_name, home_team, away_team = event.event, event.home_team, event.away_team
                commence_time = event.commence_time
                positive_play_price = outcome.line_with_pev.price
                positive_play_name = outcome.line_with_pev.name
                positive_play_percentage = outcome.positive_ev_percentage
                sport, book, bet_type = event.sport, outcome.book, outcome.bet_type
                if outcome.line_with_pev == outcome.negative_line:
                    opposing_play_price = outcome.positive_line.price
                else:
                    opposing_play_price = outcome.negative_line.price
                no_vig_probability = outcome.line_with_pev.no_vig_probability
                pev_line_probability = outcome.line_with_pev.probability

                pev_insert_command = ("INSERT INTO pev_data (uid, event_uid, event, home_team, away_team, "
                                      "commence_time, positive_play_price, positive_play_name, "
                                      "positive_play_percentage, sport, book, opposing_play_price, "
                                      "no_vig_probability, pev_line_probability, bet_type) VALUES (%s, %s, %s, %s, %s,"
                                      " %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                pev_insert_data = (uid, event_uid, event_name, home_team, away_team, commence_time, positive_play_price,
                                   positive_play_name, positive_play_percentage, sport, book, opposing_play_price,
                                   no_vig_probability, pev_line_probability, bet_type)
                cur.execute(pev_insert_command, pev_insert_data)

    print("The total number of positive ev plays was: ", total_pev_index, "/", total_outcome_index)
    print("The total number of top percent plays was: ", top_pev_index, "/", total_outcome_index)

    # Now that we have hit the mid-point of finding the averages, this feels like a good place to stop. Test this and
    # make sure that you are actually getting average values out before continuing. There is a lot of weird stuff with
    # how the arrays are stacked, so I get the creeping feeling that there may be some issues there with that.

    # Now go through each event and find the average positive and negative line value

# Finally, check to see which lines have a positive expected value from any of the lines.


def ev_main(connection, cursor, all_markets, all_lines):
    """
    This is the main file function that manages the interaction with the server file as well as the database connections
    :param cursor:
    :param connection:
    :param all_markets:
    :param all_lines:
    :return:
    """

    pev_table_delete_sql = "DELETE FROM pev_data"
    cursor.execute(pev_table_delete_sql)

    # First, call the line manager to get the events and sort the lines
    event_array = line_manager(cursor, all_markets, all_lines)

    # Next, call the main loop to complete the functionality
    pev_main_loop(event_array, cursor)

    # Finally, commit the changes to the database connection
    connection.commit()
