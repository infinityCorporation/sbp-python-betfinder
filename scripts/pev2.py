# Library Imports
import uuid
from psycopg2.extras import execute_values

# Method imports
from scripts.utilities import pull_event_lines, compare_lines

# Class Imports
from scripts.classes.eventClass import Event
from scripts.classes.outcomeClass import Outcome


def line_manager( all_markets, all_lines):
    """
    This new version of the line manager attempts to get all the lines of an event into two arrays within an event
    object
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
            returned_line = next((bet for bet in all_lines if bet['uid'] == line), None)

            if returned_line and returned_line is not None:
                positive_line, negative_line = compare_lines(returned_line['outcomes'][0], returned_line['outcomes'][1])
                outcome_object = Outcome(returned_line['uid'], returned_line['book'], positive_line, positive_line.uid, negative_line,
                                         negative_line.uid, returned_line['key'])
                pair_array.append(outcome_object)

        if len(pair_array) > 0:
            total_array.append(Event(event['uid'], event['event'], event['commence_time'], event['sport_name'], home_team, away_team, pair_array))

    return total_array


def pev_bulk_insert(pev_insert_array, cur):
    """
    Bulk insert PEV data into the pev_data table using execute_values for performance.
    """
    sql = """
    INSERT INTO pev_data (
        uid, event_uid, event, home_team, away_team,
        commence_time, positive_play_price, positive_play_name,
        positive_play_percentage, sport, book, opposing_play_price,
        no_vig_probability, pev_line_probability, bet_type,
        avg_positive_probability, avg_negative_probability, play_probability,
        avg_positive_vigged_probability, avg_negative_vigged_probability
    ) VALUES %s
    """

    values = [
        (
            x["uid"],
            x["event_uid"],
            x["event"],
            x["home_team"],
            x["away_team"],
            x["commence_time"],
            x["positive_play_price"],
            x["positive_play_name"],
            x["positive_play_percentage"],
            x["sport"],
            x["book"],
            x["opposing_play_price"],
            x["no_vig_probability"],
            x["pev_line_probability"],
            x["bet_type"],
            x["avg_positive_prob"],
            x["avg_negative_prob"],
            x["play_probability"],
            x["avg_positive_vigged_probability"],
            x["avg_negative_vigged_probability"],
        )
        for x in pev_insert_array
    ]

    execute_values(cur, sql, values)
    print(f"{len(values)} PEV entries inserted.")


def pev_main_loop(events, cur):
    """
    This is the main functionality loop for the updated pev method, slightly longer than the previous main loop
    :param events:
    :param cur:
    :return:
    """
    total_pev_index, total_outcome_index, top_pev_index = 0, 0, 0
    insert_array = []

    # First, process the event. This process each outcome, the +/- arrays, and the averages
    for event in events:
        event.process_event()

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

        if event.positive_ev_outcomes:
            prob_map = {
                'h2h': (event.average_positive_probability_h2h, event.average_negative_probability_h2h, event.average_positive_vigged_probability_h2h, event.average_negative_vigged_probability_h2h),
                'totals': (event.average_positive_probability_totals, event.average_negative_probability_totals, event.average_positive_vigged_probability_totals, event.average_negative_vigged_probability_totals),
                'spreads': (event.average_positive_probability_spreads, event.average_negative_probability_spreads, event.average_positive_vigged_probability_spreads, event.average_negative_vigged_probability_spreads)
            }

            for outcome in event.positive_ev_outcomes:
                opposing_play_price = (
                    outcome.positive_line.price if outcome.line_with_pev == outcome.negative_line
                    else outcome.negative_line.price
                )

                avg_positive_prob, avg_negative_prob, avg_pos_vigged_prob, avg_neg_vigged_prob = prob_map.get(outcome.bet_type, (0, 0, 0, 0))

                insert_array.append({
                    "uid": str(uuid.uuid4()),
                    "event_uid": event.uid,
                    "event": event.event,
                    "home_team": event.home_team,
                    "away_team": event.away_team,
                    "commence_time": event.commence_time,
                    "positive_play_price": outcome.line_with_pev.price,
                    "positive_play_name": outcome.line_with_pev.name,
                    "positive_play_percentage": abs(outcome.positive_ev_percentage),
                    "sport": event.sport,
                    "book": outcome.book,
                    "opposing_play_price": opposing_play_price,
                    "no_vig_probability": outcome.line_with_pev.no_vig_probability,
                    "pev_line_probability": outcome.line_with_pev.probability,
                    "bet_type": outcome.bet_type,
                    "avg_positive_prob": abs(avg_positive_prob),
                    "avg_negative_prob": abs(avg_negative_prob),
                    "play_probability": outcome.line_with_pev.no_vig_probability,
                    "avg_positive_vigged_probability": abs(avg_pos_vigged_prob),
                    "avg_negative_vigged_probability": abs(avg_neg_vigged_prob),
                })

    pev_bulk_insert(insert_array, cur)

    print("The total number of positive ev plays was: ", total_pev_index, "/", total_outcome_index)
    print("The total number of top percent plays was: ", top_pev_index, "/", total_outcome_index)


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
    event_array = line_manager(all_markets, all_lines)

    # Next, call the main loop to complete the functionality
    pev_main_loop(event_array, cursor)

    # Finally, commit the changes to the database connection
    connection.commit()
