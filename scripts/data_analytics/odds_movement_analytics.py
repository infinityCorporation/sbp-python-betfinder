# The goal here is to take the moneyline, spread, and total bets for each team and average them, then add
# them to the table with a timestamp. The object should look something like this:

# {
# bet_type: h2h,
# average_odds: -122,
# update_time: [current_time],
# time_til_game: [commence_time] - [current_time],
# }

def parse_odds(team_odds):
    """
    The goal is to take in the event objects from the data import and sort them into teams. From there
    we want to find the average of each of the plays based on whether its h2h, spread, or total. Then
    return a list of h2h and such
    :param team_odds:
    :return:
    """


def main(team_data):
    # first we need to get the raw team data from the import
    # get team data here

    team_odds_parsed = []

    # Here we want to parse the odds into the averages for each team
    team_odds = parse_odds(team_data)

    # then we want to store those averages in the database
    store_team_odds(team_data)
