# This is the third positive EV and implementing the second method for finding positive EV bets.

# Classes are complete as of 5/23/24. Now the final goal is to two part. First, test the class functionality. Next,
# the goal is to create a system to compare the lines in each outcome against the opposing average and then pull the
# necessary details if it presents a positive EV opportunity.


import uuid
import numpy as np
from scripts.utilities import pull_event_lines, compare_lines
from scripts.FunctionalTesting.class_test import Event
from scripts.classes.eventClass import Event
from scripts.classes.outcomeClass import Outcome
from scripts.classes.lineClass import Line

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

    # Consider, at some point in the future, moving this to a stored procedure
    pull_all_sql = "SELECT * FROM all_data"
    cur.execute(pull_all_sql)

    all_array = cur.fetchall()

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

            if returned_line and returned_line is not None:

                print("The current line is: " + returned_line[3][0][0]['name'])

                positive_line, negative_line = compare_lines(returned_line[3][0][0], returned_line[3][0][1])

                outcome_object = Outcome(returned_line[0], returned_line[5], positive_line, negative_line)
                pair_array.append(outcome_object)

        # This is not in reference of returned line
        if len(pair_array) > 0:
            total_array.append(Event(event[0], event[1], event[2], event[7], home_team, away_team, pair_array))

    return total_array


def pev_main_loop(events):
    """
    This is the main functionality loop for the updated pev method, slightly longer than the previous main loop
    :param events:
    :return:
    """

    # First, process the event. This process each outcome, the +/- arrays, and the averages
    for event in events:
        event.process_event()

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

    print("You are running pev2... ")

    # First, call the line manager to get the events and sort the lines
    event_array, event_object_array = line_manager(cursor)

    print("The line manager has run successfully... ")
    print("------------")
    print(event_array)

    print("------------")
    print("------------")
    print("The object array you are looking for is: ")
    print("------------")
    print("------------")
    print(event_object_array)
    print("------------")
    print("------------")

    for event in event_object_array:
        print("A single object is: ")
        print("------------")
        print("------------")
        print(event.event_cleaner())
        print("------------")
        print("------------")

    print("------------")
    print("------------")

    # Prevailing issues here: There are way to many event instances, like way too many. Additionally, I think
    # that this could point to a problem in the way that I am pulling and/or saving data from the api. It could
    # also be something in this file but I have my doubts about that. Check the db and see what is up.

    # Next, call the main loop to complete the functionality
    pev_main_loop(event_array)


    return

