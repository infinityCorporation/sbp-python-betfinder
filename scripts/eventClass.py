class Event:
    def __init__(self, uid, event, commence_time, sport, home_team, away_team, pair_array, positive_array,
                 negative_array, average_positive, average_negative, lines):
        self.uid = uid
        self.event = event
        self.commence_time = commence_time
        self.sport = sport
        self.home_team = home_team
        self.away_team = away_team
        self.pair_array = pair_array
        self.positive_array = positive_array
        self.negative_array = negative_array
        self.average_positive = average_positive
        self.average_negative = average_negative
        self.lines = lines

    # Maybe one of these could get rid of some of the utility function, like keep an array for the lines
    # within this class and then have a function within the class that grabs them
